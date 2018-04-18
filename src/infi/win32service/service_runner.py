import ctypes
from .service import ServiceState, ServiceControlsAccepted, SERVICE_STATUS, Service
from .common import ServiceControl, ServiceType
import six

import logging
logger = logging.getLogger(__name__)

RegisterServiceCtrlHandlerEx = ctypes.windll.advapi32.RegisterServiceCtrlHandlerExW
StartServiceCtrlDispatcher   = ctypes.windll.advapi32.StartServiceCtrlDispatcherW

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms685138%28v=VS.85%29.aspx
# VOID WINAPI ServiceMain(
#   __in  DWORD dwArgc,
#   __in  LPTSTR *lpszArgv
# );
SERVICE_MAIN_FUNCTION = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.POINTER(ctypes.c_wchar_p))

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms683241%28v=VS.85%29.aspx
# DWORD WINAPI HandlerEx(
#   __in  DWORD dwControl,
#   __in  DWORD dwEventType,
#   __in  LPVOID lpEventData,
#   __in  LPVOID lpContext
# );
# Although lpContext is LPVOID here, we specify c_ulong because we store the Pythonic context object too so it won't
# get garbage collected. We use Python's id() function as the "address" of the Pythonic context object.
# See the rest in register_ctrl_handler
HANDLER_EX = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_uint)

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms686324%28v=VS.85%29.aspx
# typedef struct _SERVICE_TABLE_ENTRY {
#   LPTSTR                  lpServiceName;
#   LPSERVICE_MAIN_FUNCTION lpServiceProc;
# } SERVICE_TABLE_ENTRY, *LPSERVICE_TABLE_ENTRY;
class SERVICE_TABLE_ENTRY(ctypes.Structure):
    _fields_ = [("lpServiceName", ctypes.c_wchar_p), ("lpServiceProc", SERVICE_MAIN_FUNCTION)]

class _ServiceCtrl(object):
    def __init__(self):
        self._garbage_protect_map = dict()
        self._contexts = dict()
        self._handles = dict()

    def register_ctrl_handler(self, service_name, callback, context=None):
        def wrapper(dwControl, dwEventType, lpEventData, lpContext):
            try:
                if dwControl == ServiceControl.DEVICEEVENT and dwEventType == EventType.POWERSETTINGCHANGE:
                    # TODO: convert lpEventData to a POWERBROADCAST_SETTING structure.
                    pass
                elif dwControl == ServiceControl.SESSIONCHANGE:
                    # TODO: convert lpEventData to WTSSESSION_NOTIFICATION structure.
                    pass
                elif dwControl == ServiceControl.TIMECHANGE:
                    # TODO: convert lpEventData to SERVICE_TIMECHANGE_INFO structure.
                    pass

                if id(wrapper) in self._handles:
                    handle = self._handles[id(wrapper)]
                else:
                    handle = None
                if lpContext in self._contexts:
                    context = self._contexts[lpContext]
                else:
                    context = None

                return callback(handle, dwControl, dwEventType, lpEventData, context)
            except:
                logger.exception("exception caught in service callback handler")

        thunk = HANDLER_EX(wrapper)

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms685058%28v=VS.85%29.aspx
        # SERVICE_STATUS_HANDLE WINAPI RegisterServiceCtrlHandlerEx(
        #   __in      LPCTSTR lpServiceName,
        #   __in      LPHANDLER_FUNCTION_EX lpHandlerProc,
        #   __in_opt  LPVOID lpContext
        # );
        handle = RegisterServiceCtrlHandlerEx(six.text_type(service_name), thunk, id(context))
        if handle == 0:
            raise ctypes.WinError()

        self._garbage_protect_map[id(thunk)] = thunk
        self._contexts[id(context)] = context
        self._handles[id(wrapper)] = handle

        return Service(handle)

    def start_ctrl_dispatcher(self, *services):
        """
        Sets the ServiceMain function of each service. Every element in the list is a pair of name and callback.

        For example:
        >>> start_service_ctrl_dispatcher(("my_service", my_service_main), ("my_other_service", my_other_service_main))

        From the MSDN docs, if the service is SERVICE_WIN32_OWN_PROCESS then the service name is ignored
        (but cannot be NULL).
        """
        # We create a NULL terminated array of pointers to SERVICE_TABLE_ENTRYs.
        service_tables = (SERVICE_TABLE_ENTRY * (len(services) + 1))()
        for i, service in enumerate(services):
            # We wrap the normal ServiceMain so we can pass the Python callback a nice argv Python array.
            def main_wrapper(argc, argv):
                try:
                    service[1](list(argv[i] for i in range(argc)))
                except:
                    logger.exception("service main exception caught")

            thunk = SERVICE_MAIN_FUNCTION(main_wrapper)
            name = six.text_type(service[0]) if service[0] is not None else ""
            service_tables[i] = SERVICE_TABLE_ENTRY(lpServiceName=name, lpServiceProc=thunk)

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms686324%28v=VS.85%29.aspx
        # BOOL WINAPI StartServiceCtrlDispatcher(
        #   __in  const SERVICE_TABLE_ENTRY *lpServiceTable
        # );
        if not StartServiceCtrlDispatcher(service_tables):
            raise ctypes.WinError()

        # We need to protect ctype's thunk from the garbage collector. Note that this is a memory "leak" because we
        # never remove it from the map, but it's okay since a service should have a single ServiceMain entry.
        for service_table in service_tables:
            self._garbage_protect_map[id(service_table.lpServiceProc)] = service_table.lpServiceProc

ServiceCtrl = _ServiceCtrl()

class ServiceRunner(object):
    def __init__(self, service_name):
        self.status = ServiceState.START_PENDING
        self.service_name = service_name

    def main(self):
        raise NotImplementedError()

    def control(self, service_control):
        raise NotImplementedError()

    def run(self):
        logger.debug("ServiceRunner.run called.")
        try:
            ServiceCtrl.start_ctrl_dispatcher((self.service_name, self._service_main))
        except:
            logger.exception("error occurred")

    def _service_main(self, args):
        logger.debug("ServiceRunner._service_main called, self=%s, args=%s" % (self, repr(args)))

        try:
            service = ServiceCtrl.register_ctrl_handler(self.service_name, self._service_callback)

            logger.debug("setting status to START_PENDING")
            self._notify_status(service, ServiceState.START_PENDING)

            logger.debug("setting status to RUNNING")
            self._notify_status(service, ServiceState.RUNNING)

            self.main()
        except:
            logger.exception("error occurred")

    def _service_callback(self, handle, fdwControl, dwEventType, lpEventData, lpContext):
        logger.debug("ServiceRunner._service_callback: handle=%x, fdwControl=%x dwEventType=%x" %
                  (handle, fdwControl, dwEventType))

        self.control(fdwControl)

        service = Service(handle)
        if fdwControl == ServiceControl.STOP:
            logger.debug("STOP requested, quitting.")
            self._notify_status(service, ServiceState.STOPPED)
        elif fdwControl == ServiceControl.INTERROGATE:
            logger.debug("INTERROGATE requested.")
            self._notify_status(service)

        return 0

    def _notify_status(self, service, status=None):
        if status is not None:
            self.status = status
        status_struct = SERVICE_STATUS(dwServiceType=ServiceType.WIN32_OWN_PROCESS,
                                       dwCurrentState=self.status,
                                       dwControlsAccepted=(ServiceControlsAccepted.STOP |
                                                           ServiceControlsAccepted.SHUTDOWN),
                                       dwWin32ExitCode=0,
                                       dwServiceSpecificExitCode=0,
                                       dwCheckPoint=0,
                                       dwWaitHint=0)
        service.set_status(status_struct)
