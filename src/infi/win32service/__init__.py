__import__("pkg_resources").declare_namespace(__name__)

import ctypes

from .service import Service

RegisterServiceCtrlHandlerEx = ctypes.windll.advapi32.RegisterServiceCtrlHandlerExW

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms683241%28v=VS.85%29.aspx
# DWORD WINAPI HandlerEx(
#   __in  DWORD dwControl,
#   __in  DWORD dwEventType,
#   __in  LPVOID lpEventData,
#   __in  LPVOID lpContext
# );
HANDLER_EX = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms683241%28v=VS.85%29.aspx
ServiceControl = enum(
    STOP                  = 0x00000001,
    PAUSE                 = 0x00000002,
    CONTINUE              = 0x00000003,
    INTERROGATE           = 0x00000004,
    SHUTDOWN              = 0x00000005,
    PARAMCHANGE           = 0x00000006,
    NETBINDADD            = 0x00000007,
    NETBINDREMOVE         = 0x00000008,
    NETBINDENABLE         = 0x00000009,
    NETBINDDISABLE        = 0x0000000A,
    DEVICEEVENT           = 0x0000000B,
    HARDWAREPROFILECHANGE = 0x0000000C,
    POWEREVENT            = 0x0000000D,
    SESSIONCHANGE         = 0x0000000E,
    PRESHUTDOWN           = 0x0000000F,
    TIMECHANGE            = 0x00000010,
    TRIGGEREVENT          = 0x00000020
    # 0x80 - 0xFF: user defined
    )

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms686324%28v=VS.85%29.aspx
# typedef struct _SERVICE_TABLE_ENTRY {
#   LPTSTR                  lpServiceName;
#   LPSERVICE_MAIN_FUNCTION lpServiceProc;
# } SERVICE_TABLE_ENTRY, *LPSERVICE_TABLE_ENTRY;
class SERVICE_TABLE_ENTRY(ctypes.Structure):
    _fields_ = [("lpServiceName", ctypes.c_wchar_p), ("lpServiceProc", ctypes.c_void_p)]

# To prevent the garbage collector from destroying the callbacks/contexts, we add them here.
_garbage_protect_map = dict()

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms685058%28v=VS.85%29.aspx
# SERVICE_STATUS_HANDLE WINAPI RegisterServiceCtrlHandlerEx(
#   __in      LPCTSTR lpServiceName,
#   __in      LPHANDLER_FUNCTION_EX lpHandlerProc,
#   __in_opt  LPVOID lpContext
# );
def register_service_ctrl_handler(self, service_name, callback, context):
    def thunk(dwControl, dwEventType, lpEventData, lpContext):
        if dwControl == ServiceControl.DEVICEEVENT and dwEventType == EventType.POWERSETTINGCHANGE:
            # convert lpEventData to a POWERBROADCAST_SETTING structure.
            pass
        elif dwControl == ServiceControl.SESSIONCHANGE:
            # convert lpEventData to WTSSESSION_NOTIFICATION structure.
            pass
        elif dwControl == ServiceControl.TIMECHANGE:
            # convert lpEventData to SERVICE_TIMECHANGE_INFO structure.
            pass
        callback(dwControl, dwEventType, lpEventDataw, lpContext)

    callback_wrapper = HANDLER_EX(thunk)
    context_wrapper = ctypes.c_void_p(context)
    handle = RegisterServiceCtrlHandlerEx(service_name, callback_wrapper, context)
    if handle == 0:
        raise ctypes.WinError()

    _garbage_protect_map[ctypes.addressof(callback_wrapper)] = callback_wrapper
    if context is not None:
        _context_list.append(context)

    return handle


# http://msdn.microsoft.com/en-us/library/windows/desktop/ms686324%28v=VS.85%29.aspx
# BOOL WINAPI StartServiceCtrlDispatcher(
#   __in  const SERVICE_TABLE_ENTRY *lpServiceTable
# );
def start_service_ctrl_dispatcher(*services):
    """
    Sets the ServiceMain function of each service. Every element in the list is a pair of name and callback.

    For example:
    >>> start_service_ctrl_dispatcher(("my_service", my_service_main), ("my_other_service", my_other_service_main))

    From the MSDN docs, if the service is SERVICE_WIN32_OWN_PROCESS then the service name is ignored
    (but cannot be NULL).
    """

    # We create here a NULL terminated array.
    service_tables = (SERVICE_TABLE_ENTRY * (len(service_tables) + 1))((SERVICE_TABLE_ENTRY(services)
    

#class ServiceHandler(object):
#    def init(self):
        
