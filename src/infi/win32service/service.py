import ctypes
import logging

from .utils import enum
from .common import ServiceControl, ServiceType

StartService                 = ctypes.windll.advapi32.StartServiceW
ControlService               = ctypes.windll.advapi32.ControlService
DeleteService                = ctypes.windll.advapi32.DeleteService
SetServiceStatus             = ctypes.windll.advapi32.SetServiceStatus
CloseServiceHandle           = ctypes.windll.advapi32.CloseServiceHandle
RegisterServiceCtrlHandlerEx = ctypes.windll.advapi32.RegisterServiceCtrlHandlerExW
StartServiceCtrlDispatcher   = ctypes.windll.advapi32.StartServiceCtrlDispatcherW

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

class Service(object):
    def __init__(self, handle, tag=None):
        self.handle = handle
        self.tag = tag

    def start(self, *args):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms686321%28v=vs.85%29.aspx
        # BOOL WINAPI StartService(
        #   __in      SC_HANDLE hService,
        #   __in      DWORD dwNumServiceArgs,
        #   __in_opt  LPCTSTR *lpServiceArgVectors
        # );
        lpServiceArgVectors = (ctypes.c_wchar_p * len(args))(*args)
        if not StartService(self.handle, len(args), lpServiceArgVectors):
            raise ctypes.WinError()

    def stop(self):
        """
        Stops the service.
        """
        new_status = SERVICE_STATUS()
        if not ControlService(self.handle, ServiceControl.STOP, ctypes.byref(new_status)):
            raise ctypes.WinError()
        if new_status.dwCurrentState not in [ServiceState.STOPPED, ServiceState.STOP_PENDING]:
            raise ctypes.WinError()
        
    def safe_stop(self):
        """
        Stops the service, and ignores "not started" errors
        """
        try:
            self.stop()
        except WindowsError, e:
            if e.winerror != 1062:
                raise

    def query_config(self):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms684932%28v=vs.85%29.aspx
        # BOOL WINAPI QueryServiceConfig(
        #   __in       SC_HANDLE hService,
        #   __out_opt  LPQUERY_SERVICE_CONFIG lpServiceConfig,
        #   __in       DWORD cbBufSize,
        #   __out      LPDWORD pcbBytesNeeded
        # );
        raise NotImplementedError()

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
                raise ctypes.WinError()
            self.handle = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

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
                logging.exception("exception caught in service callback handler")
            
        thunk = HANDLER_EX(wrapper)

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms685058%28v=VS.85%29.aspx
        # SERVICE_STATUS_HANDLE WINAPI RegisterServiceCtrlHandlerEx(
        #   __in      LPCTSTR lpServiceName,
        #   __in      LPHANDLER_FUNCTION_EX lpHandlerProc,
        #   __in_opt  LPVOID lpContext
        # );
        handle = RegisterServiceCtrlHandlerEx(unicode(service_name), thunk, id(context))
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
        for service, i in zip(services, xrange(len(services))):
            # We wrap the normal ServiceMain so we can pass the Python callback a nice argv Python array.
            def main_wrapper(argc, argv):
                try:
                    service[1](list(argv[i] for i in xrange(argc)))
                except:
                    logging.exception("service main exception caught")

            thunk = SERVICE_MAIN_FUNCTION(main_wrapper)
            name = unicode(service[0]) if service[0] is not None else u""
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
