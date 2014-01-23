from unittest import TestCase
from threading import Event
import os
import time
from infi.win32service import ServiceControlManagerContext, ServiceRunner, ServiceType, ServiceStartType, ServiceControl
import logging
import tempfile

INFI_SERVICE_NAME = u"InfinidatTest"
TEST_FILE = "c:\\test_service.txt"

class TestWin32Service(TestCase):
    def _register(self):
        with ServiceControlManagerContext() as scm:
            python_exe = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "bin", "python.exe"))
            scm.create_service(INFI_SERVICE_NAME,
                               u"Infinidat Test Service",
                               ServiceType.WIN32_OWN_PROCESS,
                               ServiceStartType.AUTO,
                               "\"{}\" {}".format(python_exe, __file__.replace('.pyc', '.py'))).close()

    def _start_stop(self):
        with ServiceControlManagerContext() as scm:
            infi_service = scm.open_service(INFI_SERVICE_NAME)
            infi_service.start()
            time.sleep(3)
            self.assertTrue(infi_service.is_running())
            infi_service.stop()
            time.sleep(6)
            self.assertFalse(infi_service.is_running())
            infi_service.close()

    def _stop(self):
        with ServiceControlManagerContext() as scm:
            infi_service = scm.open_service(INFI_SERVICE_NAME)
            with infi_service:
                infi_service.safe_stop()
                time.sleep(6)

    def _delete(self):
        with ServiceControlManagerContext() as scm:
            infi_service = scm.open_service(INFI_SERVICE_NAME)
            infi_service.delete()
            infi_service.close()

        # sleep to let the service db refresh or something; otherwise the open succeeds, somehow, sometimes
        time.sleep(3)

        with ServiceControlManagerContext() as scm:
            with self.assertRaisesRegexp(WindowsError, "The specified service does not exist as an installed service."):
                infi_service = scm.open_service(INFI_SERVICE_NAME)

    def test_full_cycle(self):
        self._register()
        self._start_stop()

        test_lines = open(TEST_FILE, "rb").readlines()
        self.assertEqual(test_lines, ["started\n", "stopped\n"])

        self._delete()

    def test_stop_twice(self):
        with ServiceControlManagerContext() as scm:
            infi_service = scm.open_service("VSS")
            with infi_service:
                infi_service.safe_stop()
                time.sleep(6)
        with ServiceControlManagerContext() as scm:
            infi_service = scm.open_service("VSS")
            with infi_service:
                infi_service.safe_stop()
                time.sleep(6)

class MyServiceRunner(ServiceRunner):
    def __init__(self):
        super(MyServiceRunner, self).__init__(INFI_SERVICE_NAME)
        self._stop_event = Event()

    def main(self):
        test_file = open(TEST_FILE, "wb")
        test_file.write("started\n")
        self._stop_event.wait()
        test_file.write("stopped\n")
        test_file.close()

    def control(self, control):
        if control == ServiceControl.STOP:
            self._stop_event.set()
        # sleep before returning control to service runner and notifying that we are stopped - gives the main
        # thread time to exit gracefully before it will be killed by the Windows service manager after notification
        time.sleep(3)

if __name__ == "__main__":
    MyServiceRunner().run()
