import ctypes
import logging
import six

from .utils import enum
from .common import ServiceControl, ServiceType, ERROR_INVALID_HANDLE

StartService                 = ctypes.windll.advapi32.StartServiceW
ControlService               = ctypes.windll.advapi32.ControlService
DeleteService                = ctypes.windll.advapi32.DeleteService
SetServiceStatus             = ctypes.windll.advapi32.SetServiceStatus
CloseServiceHandle           = ctypes.windll.advapi32.CloseServiceHandle
QueryServiceStatus           = ctypes.windll.advapi32.QueryServiceStatus
QueryServiceConfig           = ctypes.windll.advapi32.QueryServiceConfigW
ChangeServiceConfig          = ctypes.windll.advapi32.ChangeServiceConfigW

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
    _fields_ = [("dwServiceType", ctypes.c_ulong),
                ("dwCurrentState", ctypes.c_ulong),
                ("dwControlsAccepted", ctypes.c_ulong),
                ("dwWin32ExitCode", ctypes.c_ulong),
                ("dwServiceSpecificExitCode", ctypes.c_ulong),
                ("dwCheckPoint", ctypes.c_ulong),
                ("dwWaitHint", ctypes.c_ulong),
                ("dwProcessId", ctypes.c_ulong),
                ("dwServiceFlags", ctypes.c_ulong)]

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
    _fields_ = [("dwServiceType", ctypes.c_ulong),
                ("dwStartType", ctypes.c_ulong),
                ("dwErrorControl", ctypes.c_ulong),
                ("lpBinaryPathName", ctypes.c_wchar_p),
                ("lpLoadOrderGroup", ctypes.c_wchar_p),
                ("dwTagId", ctypes.c_ulong),
                ("lpDependencies", ctypes.c_wchar_p),
                ("lpServiceStartName", ctypes.c_wchar_p)]

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
    _fields_ = [("dwServiceType", ctypes.c_ulong),
                ("dwCurrentState", ctypes.c_ulong),
                ("dwControlsAccepted", ctypes.c_ulong),
                ("dwWin32ExitCode", ctypes.c_ulong),
                ("dwServiceSpecificExitCode", ctypes.c_ulong),
                ("dwCheckPoint", ctypes.c_ulong),
                ("dwWaitHint", ctypes.c_ulong)]

LPSERVICE_STATUS = ctypes.POINTER(SERVICE_STATUS)

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms685947%28v=VS.85%29.aspx
# typedef VOID( CALLBACK * PFN_SC_NOTIFY_CALLBACK ) (
#     IN PVOID pParameter
# );
FN_SC_NOTIFY_CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p)

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms685947%28v=VS.85%29.aspx
# typedef struct _SERVICE_NOTIFY {
#   DWORD                  dwVersion;
#   PFN_SC_NOTIFY_CALLBACK pfnNotifyCallback;
#   PVOID                  pContext;
#   DWORD                  dwNotificationStatus;
#   SERVICE_STATUS_PROCESS ServiceStatus;
#   DWORD                  dwNotificationTriggered;
#   LPTSTR                 pszServiceNames;
# } SERVICE_NOTIFY, *PSERVICE_NOTIFY;
class SERVICE_NOTIFY(ctypes.Structure):
    _fields_ = [("dwVersion", ctypes.c_ulong),
                ("pfnNotifyCallback", FN_SC_NOTIFY_CALLBACK),
                ("pContext", ctypes.c_void_p),
                ("dwNotificationStatus", ctypes.c_ulong),
                ("ServiceStatus", SERVICE_STATUS_PROCESS),
                ("dwNotificationTriggered", ctypes.c_ulong),
                ("pszServiceNames", ctypes.c_wchar_p)]

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

class Service(object):
    def __init__(self, handle, tag=None):
        self.handle = ctypes.c_void_p(handle) if isinstance(handle, six.integer_types) else \
                      ctypes.c_void_p(handle.value) if hasattr(handle, value) else handle
        self.tag = tag

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
            lpServiceArgVectors = (ctypes.c_wchar_p * len(args))(*args)
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
        bytes_needed = ctypes.c_ulong()
        if not QueryServiceConfig(self.handle, config_buffer, 8192, ctypes.byref(bytes_needed)):
            raise ctypes.WinError()
        service_config = ctypes.cast(config_buffer, ctypes.POINTER(QUERY_SERVICE_CONFIG))
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
        null_ptr = ctypes.POINTER(ctypes.c_int)()
        if not ChangeServiceConfig(self.handle,
                                   SERVICE_NO_CHANGE, start_type, SERVICE_NO_CHANGE,
                                   null_ptr, null_ptr,
                                   null_ptr, null_ptr, null_ptr,
                                   null_ptr, null_ptr):
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
                if ctypes.GetLastError() != ERROR_INVALID_HANDLE:
                    raise ctypes.WinError()
            self.handle = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
