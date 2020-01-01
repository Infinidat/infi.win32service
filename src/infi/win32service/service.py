import ctypes
from ctypes import wintypes
import logging
import six

from .utils import enum
from .common import ServiceControl, ServiceType, ERROR_INVALID_HANDLE

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms685992%28v=VS.85%29.aspx
# typedef struct _SERVICE_STATUS_PROCESS {
#   DWORD dwServiceType;
#   DWORD dwCurrentState;
#   DWORD dwControlsAccepted;
#   DWORD dwWin32ExitCode;
#   DWORD dwServiceSpecificExitCode;
#   DWORD dwCheckPoint;
#   DWORD dwWaitHint;
#   DWORD dwProcessId;
#   DWORD dwServiceFlags;
# } SERVICE_STATUS_PROCESS, *LPSERVICE_STATUS_PROCESS;
class SERVICE_STATUS_PROCESS(ctypes.Structure):
    _fields_ = [("dwServiceType", wintypes.DWORD),
                ("dwCurrentState", wintypes.DWORD),
                ("dwControlsAccepted", wintypes.DWORD),
                ("dwWin32ExitCode", wintypes.DWORD),
                ("dwServiceSpecificExitCode", wintypes.DWORD),
                ("dwCheckPoint", wintypes.DWORD),
                ("dwWaitHint", wintypes.DWORD),
                ("dwProcessId", wintypes.DWORD),
                ("dwServiceFlags", wintypes.DWORD)]

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms684950(v=vs.85).aspx
# typedef struct _QUERY_SERVICE_CONFIG {
#   DWORD  dwServiceType;
#   DWORD  dwStartType;
#   DWORD  dwErrorControl;
#   LPTSTR lpBinaryPathName;
#   LPTSTR lpLoadOrderGroup;
#   DWORD  dwTagId;
#   LPTSTR lpDependencies;
#   LPTSTR lpServiceStartName;
#   LPTSTR lpDisplayName;
# } QUERY_SERVICE_CONFIG, *LPQUERY_SERVICE_CONFIG;
class QUERY_SERVICE_CONFIG(ctypes.Structure):
    _fields_ = [("dwServiceType", wintypes.DWORD),
                ("dwStartType", wintypes.DWORD),
                ("dwErrorControl", wintypes.DWORD),
                ("lpBinaryPathName", wintypes.LPWSTR),
                ("lpLoadOrderGroup", wintypes.LPWSTR),
                ("dwTagId", wintypes.DWORD),
                ("lpDependencies", wintypes.LPWSTR),
                ("lpServiceStartName", wintypes.LPWSTR),
                ("lpDisplayName", wintypes.LPWSTR),]

    def to_dict(self):
        return dict(service_type=self.dwServiceType, start_type=self.dwStartType,
                    error_control=self.dwErrorControl, binary_path_name=self.lpBinaryPathName,
                    load_order_group=self.lpLoadOrderGroup, tag_id=self.dwTagId,
                    dependencies=self.lpDependencies, service_start_name=self.lpServiceStartName)


LPQUERY_SERVICE_CONFIG = ctypes.POINTER(QUERY_SERVICE_CONFIG)

# From http://msdn.microsoft.com/en-us/library/windows/desktop/ms685996%28v=vs.85%29.aspx

ServiceState = enum(
    STOPPED          = 0x00000001,
    START_PENDING    = 0x00000002,
    STOP_PENDING     = 0x00000003,
    RUNNING          = 0x00000004,
    CONTINUE_PENDING = 0x00000005,
    PAUSE_PENDING    = 0x00000006,
    PAUSED           = 0x00000007
)

ServiceControlsAccepted = enum(
    STOP                  = 0x00000001,
    SHUTDOWN              = 0x00000004,
    PARAMCHANGE           = 0x00000008,
    PAUSE_CONTINUE        = 0x00000002,
    NETBINDCHANGE         = 0x00000010,
    HARDWAREPROFILECHANGE = 0x00000020,
    POWEREVENT            = 0x00000040,
    SESSIONCHANGE         = 0x00000080,
    PRESHUTDOWN           = 0x00000100,
    TIMECHANGE            = 0x00000200,
    TRIGGEREVENT          = 0x00000400
)


ServiceType = enum(
    SERVICE_KERNEL_DRIVER = 0x00000001,
    SERVICE_FILE_SYSTEM_DRIVER = 0x00000002,
    SERVICE_WIN32_OWN_PROCESS = 0x00000010,
    SERVICE_WIN32_SHARE_PROCESS = 0x00000020
)

StartType = enum(
SERVICE_BOOT_START = 0x00000000,
SERVICE_SYSTEM_START = 0x00000001,
SERVICE_AUTO_START = 0x00000002,
SERVICE_DEMAND_START = 0x00000003,
SERVICE_DISABLED = 0x00000004
)

# typedef struct _SERVICE_STATUS {
#   DWORD dwServiceType;
#   DWORD dwCurrentState;
#   DWORD dwControlsAccepted;
#   DWORD dwWin32ExitCode;
#   DWORD dwServiceSpecificExitCode;
#   DWORD dwCheckPoint;
#   DWORD dwWaitHint;
# } SERVICE_STATUS, *LPSERVICE_STATUS;
class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [("dwServiceType", wintypes.DWORD),
                ("dwCurrentState", wintypes.DWORD),
                ("dwControlsAccepted", wintypes.DWORD),
                ("dwWin32ExitCode", wintypes.DWORD),
                ("dwServiceSpecificExitCode", wintypes.DWORD),
                ("dwCheckPoint", wintypes.DWORD),
                ("dwWaitHint", wintypes.DWORD)]

LPSERVICE_STATUS = ctypes.POINTER(SERVICE_STATUS)

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms684276%28v=VS.85%29.aspx
ServiceNotifyMask = enum(
    STOPPED          = 0x00000001,
    START_PENDING    = 0x00000002,
    STOP_PENDING     = 0x00000004,
    RUNNING          = 0x00000008,
    CONTINUE_PENDING = 0x00000010,
    PAUSE_PENDING    = 0x00000020,
    PAUSED           = 0x00000040,
    CREATED          = 0x00000080,
    DELETED          = 0x00000100,
    DELETE_PENDING   = 0x00000200
)

# From WinError.h:
ERROR_SERVICE_SPECIFIC_ERROR = 1066
NO_ERROR = 0

# From winsvc.h:
SERVICE_NO_CHANGE = 0xffffffff


StartService = ctypes.windll.advapi32.StartServiceW
StartService.argtypes = (wintypes.SC_HANDLE, wintypes.DWORD, wintypes.LPCWSTR)
StartService.restype = wintypes.BOOL
ControlService = ctypes.windll.advapi32.ControlService
ControlService.argtypes = (wintypes.SC_HANDLE, wintypes.DWORD, LPSERVICE_STATUS)
ControlService.restype = wintypes.BOOL
DeleteService = ctypes.windll.advapi32.DeleteService
DeleteService.argtypes = (wintypes.SC_HANDLE, )
DeleteService.restype = wintypes.BOOL
SetServiceStatus = ctypes.windll.advapi32.SetServiceStatus
SetServiceStatus.argtypes = (wintypes.SERVICE_STATUS_HANDLE, LPSERVICE_STATUS)
SetServiceStatus.restype = wintypes.BOOL
CloseServiceHandle = ctypes.windll.advapi32.CloseServiceHandle
CloseServiceHandle.argtypes = (wintypes.SC_HANDLE, )
CloseServiceHandle.restype = wintypes.BOOL
QueryServiceStatus = ctypes.windll.advapi32.QueryServiceStatus
QueryServiceStatus.argtypes = (wintypes.SC_HANDLE, LPSERVICE_STATUS)
QueryServiceStatus.restype = wintypes.BOOL
QueryServiceConfig = ctypes.windll.advapi32.QueryServiceConfigW
QueryServiceConfig.argtypes = (wintypes.SC_HANDLE, LPQUERY_SERVICE_CONFIG, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
QueryServiceConfig.restype = wintypes.BOOL
ChangeServiceConfig = ctypes.windll.advapi32.ChangeServiceConfigW
ChangeServiceConfig.argtypes = (wintypes.SC_HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                                wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD),
                                wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR)
ChangeServiceConfig.restype = wintypes.BOOL


class Service(object):
    def __init__(self, handle):
        self.handle = wintypes.SC_HANDLE(handle) if isinstance(handle, six.integer_types) else \
                      wintypes.SC_HANDLE(handle.value) if hasattr(handle, "value") else handle

    def start(self, *args):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms686321%28v=vs.85%29.aspx
        # BOOL WINAPI StartService(
        #   __in      SC_HANDLE hService,
        #   __in      DWORD dwNumServiceArgs,
        #   __in_opt  LPCTSTR *lpServiceArgVectors
        # );
        if len(args) == 0:
            lpServiceArgVectors = None
        else:
            lpServiceArgVectors = (wintypes.LPWSTR * len(args))(*args)
        if not StartService(self.handle, len(args), lpServiceArgVectors):
            raise ctypes.WinError()

    def wait_on_pending(self, timeout_in_seconds=60):
        from time import sleep
        for sec in range(timeout_in_seconds):
            if self.get_status() in (ServiceState.STOP_PENDING, ServiceState.START_PENDING):
                sleep(1)
            else:
                return
        raise RuntimeError("wait_on_pending timed out, status is: {}".format(self.get_status()))

    def stop(self):
        """
        Stops the service.
        """
        new_status = SERVICE_STATUS()
        if not ControlService(self.handle, ServiceControl.STOP, ctypes.byref(new_status)):
            raise ctypes.WinError()
        if new_status.dwCurrentState not in [ServiceState.STOPPED, ServiceState.STOP_PENDING]:
            raise ctypes.WinError()

    def safe_start(self):
        if self.get_status() in [ServiceState.RUNNING, ServiceState.START_PENDING]:
            return
        self.start()

    def safe_stop(self):
        """
        Stops the service, and ignores "not started" errors
        """
        if self.get_status() in [ServiceState.STOPPED, ServiceState.STOP_PENDING]:
            return
        try:
            self.stop()
        except WindowsError as e:
            if e.winerror != 1062:
                raise

    def get_status(self):
        current_status = SERVICE_STATUS()
        if not QueryServiceStatus(self.handle, ctypes.byref(current_status)):
            raise ctypes.WinError()
        return current_status.dwCurrentState

    def is_running(self):
        return self.get_status() == ServiceState.RUNNING

    # def change_service_config
    # https://msdn.microsoft.com/en-us/library/windows/desktop/ms681987(v=vs.85).aspx

    def query_config(self):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms684932%28v=vs.85%29.aspx
        # BOOL WINAPI QueryServiceConfig(
        #   __in       SC_HANDLE hService,
        #   __out_opt  LPQUERY_SERVICE_CONFIG lpServiceConfig,
        #   __in       DWORD cbBufSize,
        #   __out      LPDWORD pcbBytesNeeded
        # );
        config_buffer = ctypes.create_string_buffer(8192) # The maximum size of this array is 8K bytes
        bytes_needed = wintypes.DWORD()
        service_config = ctypes.cast(config_buffer, ctypes.POINTER(QUERY_SERVICE_CONFIG))
        if not QueryServiceConfig(self.handle, service_config, 8192, ctypes.byref(bytes_needed)):
            raise ctypes.WinError()
        return service_config.contents.to_dict()

    def change_service_config(self, start_type):
        # https://msdn.microsoft.com/en-us/library/windows/desktop/ms681987(v=vs.85).aspx
        # BOOL WINAPI ChangeServiceConfig(
        #   _In_      SC_HANDLE hService,
        #   _In_      DWORD     dwServiceType,
        #   _In_      DWORD     dwStartType,
        #   _In_      DWORD     dwErrorControl,
        #   _In_opt_  LPCTSTR   lpBinaryPathName,
        #   _In_opt_  LPCTSTR   lpLoadOrderGroup,
        #   _Out_opt_ LPDWORD   lpdwTagId,
        #   _In_opt_  LPCTSTR   lpDependencies,
        #   _In_opt_  LPCTSTR   lpServiceStartName,
        #   _In_opt_  LPCTSTR   lpPassword,
        #   _In_opt_  LPCTSTR   lpDisplayName
        # );
        if not ChangeServiceConfig(self.handle,
                                   SERVICE_NO_CHANGE, start_type, SERVICE_NO_CHANGE,
                                   None, None,
                                   None, None, None,
                                   None, None):
            raise ctypes.WinError()

    def is_disabled(self):
        return self.query_config()['start_type'] == StartType.SERVICE_DISABLED

    def is_autostart(self):
        return self.query_config()['start_type'] == StartType.SERVICE_AUTO_START

    def disable(self):
        self.change_service_config(StartType.SERVICE_DISABLED)

    def start_automatically(self):
        self.change_service_config(StartType.SERVICE_AUTO_START)

    def query_optional_config(self):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms684935%28v=VS.85%29.aspx
        # BOOL WINAPI QueryServiceConfig2(
        #   __in       SC_HANDLE hService,
        #   __in       DWORD dwInfoLevel,
        #   __out_opt  LPBYTE lpBuffer,
        #   __in       DWORD cbBufSize,
        #   __out      LPDWORD pcbBytesNeeded
        # );
        raise NotImplementedError()

    def set_status(self, status):
        """
        Sets the service status. status argument must be a SERVICE_STATUS object.
        """
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms686241%28v=VS.85%29.aspx
        # BOOL WINAPI SetServiceStatus(
        #   __in  SERVICE_STATUS_HANDLE hServiceStatus,
        #   __in  LPSERVICE_STATUS lpServiceStatus
        # );
        if not SetServiceStatus(self.handle, LPSERVICE_STATUS(status)):
            raise ctypes.WinError()

    def delete(self):
        """
        Deletes the service.
        """
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms682562%28v=vs.85%29.aspx
        # BOOL WINAPI DeleteService(
        #   __in  SC_HANDLE hService
        # );
        if not DeleteService(self.handle):
            raise ctypes.WinError()

    def close(self):
        if self.handle != 0:
            if not CloseServiceHandle(self.handle):
                if ctypes.get_last_error() != ERROR_INVALID_HANDLE:
                    raise ctypes.WinError()
            self.handle = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
