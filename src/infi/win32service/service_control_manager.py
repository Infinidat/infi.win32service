import ctypes
from ctypes import wintypes
from collections import namedtuple
import six

from .utils import enum
from .service import Service
from .common import ServiceType, ERROR_INVALID_HANDLE

OpenSCManager = ctypes.windll.advapi32.OpenSCManagerW
OpenSCManager.argtypes = (wintypes.LPWSTR, wintypes.LPWSTR, wintypes.DWORD)
OpenSCManager.restype = wintypes.SC_HANDLE
OpenService = ctypes.windll.advapi32.OpenServiceW
OpenService.argtypes = (wintypes.SC_HANDLE, wintypes.LPWSTR, wintypes.DWORD)
OpenService.restype = wintypes.SC_HANDLE
CloseServiceHandle = ctypes.windll.advapi32.CloseServiceHandle
CloseServiceHandle.argtypes = (wintypes.SC_HANDLE, )
CloseServiceHandle.restype = wintypes.BOOL
CreateService = ctypes.windll.advapi32.CreateServiceW
CreateService.argtypes = (wintypes.SC_HANDLE, wintypes.LPCWSTR, wintypes.LPCWSTR,
                          wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                          wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD),
                          wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR)
CreateService.restype = wintypes.SC_HANDLE

# From http://msdn.microsoft.com/en-us/library/windows/desktop/ms685981%28v=vs.85%29.aspx
ServiceManagerAccess = enum(
    ALL                = 0xF003F,
    CONNECT            = 0x0001,
    CREATE_SERVICE     = 0x0002,
    ENUMERATE_SERVICE  = 0x0004,
    LOCK               = 0x0008,
    QUERY_LOCK_STATUS  = 0x0010,
    MODIFY_BOOT_CONFIG = 0x0020)

# From http://msdn.microsoft.com/en-us/library/windows/desktop/ms684323%28v=vs.85%29.aspx
SC_ACTIVE_DATABASE = u"SERVICES_ACTIVE_DATABASE"

# From http://msdn.microsoft.com/en-us/library/windows/desktop/ms682450%28v=vs.85%29.aspx

# -- CreateService.dwStartType:
ServiceStartType = enum(
    BOOT     = 0x00000000,
    SYSTEM   = 0x00000001,
    AUTO     = 0x00000002,
    DEMAND   = 0x00000003,
    DISABLED = 0x00000004)

# -- CreateService.dwErrorControl:
ServiceErrorControl = enum(
    IGNORE   = 0x00000000,
    NORMAL   = 0x00000001,
    SEVERE   = 0x00000002,
    CRITICAL = 0x00000003)

# -- CreateService.dwDesiredAccess:
ServiceAccess = enum(ALL                  = 0xF01FF,
                     QUERY_CONFIG         = 0x0001,
                     CHANGE_CONFIG        = 0x0002,
                     QUERY_STATUS         = 0x0004,
                     ENUMERATE_DEPENDENTS = 0x0008,
                     START                = 0x0010,
                     STOP                 = 0x0020,
                     PAUSE_CONTINUE       = 0x0040,
                     INTERROGATE          = 0x0080,
                     USER_DEFINED_CONTROL = 0x0100)

class ServiceControlManagerContext(object):
    def __init__(self, machine=None, database=None, access=ServiceManagerAccess.ALL):
        super(ServiceControlManagerContext, self).__init__()
        self.machine = wintypes.LPWSTR(machine) if machine is not None else None
        self.database = wintypes.LPWSTR(database) if database is not None else None
        self.access = access
        self.scm = None

    def __enter__(self):
        scm_handle = OpenSCManager(self.machine, self.database, self.access)
        if scm_handle is None:
            raise ctypes.WinError()
        self.scm = ServiceControlManager(scm_handle)
        return self.scm

    def __exit__(self, type, value, traceback):
        if self.scm is not None:
            self.scm.close()

class ServiceControlManager(object):
    def __init__(self, handle):
        super(ServiceControlManager, self).__init__()
        self.handle = wintypes.SC_HANDLE(handle) if isinstance(handle, six.integer_types) else \
                      wintypes.SC_HANDLE(handle.value) if hasattr(handle, "value") else handle

    def create_service(self, name, display_name, type, start_type, path,
                       load_order_group=None, dependencies=None, error_control=ServiceErrorControl.NORMAL,
                       account=None, account_password=None, access=ServiceAccess.ALL):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms682450%28v=vs.85%29.aspx
        # SC_HANDLE WINAPI CreateService(
        #   __in       SC_HANDLE hSCManager,
        #   __in       LPCTSTR lpServiceName,
        #   __in_opt   LPCTSTR lpDisplayName,
        #   __in       DWORD dwDesiredAccess,
        #   __in       DWORD dwServiceType,
        #   __in       DWORD dwStartType,
        #   __in       DWORD dwErrorControl,
        #   __in_opt   LPCTSTR lpBinaryPathName,
        #   __in_opt   LPCTSTR lpLoadOrderGroup,
        #   __out_opt  LPDWORD lpdwTagId,
        #   __in_opt   LPCTSTR lpDependencies,
        #   __in_opt   LPCTSTR lpServiceStartName,
        #   __in_opt   LPCTSTR lpPassword
        #);
        lpServiceName = wintypes.LPWSTR(name)
        lpDisplayName = wintypes.LPWSTR(display_name)
        dwDesiredAccess = access
        dwServiceType = type
        dwStartType = start_type
        dwErrorControl = error_control
        lpBinaryPathName = wintypes.LPWSTR(path)
        lpLoadOrderGroup = wintypes.LPWSTR(load_order_group) if load_order_group is not None else None

        lpdwTagId = None    # from CreateService docs: "Specify NULL if you are not changing the existing tag."

        lpDependencies = wintypes.LPWSTR(dependencies) if dependencies is not None else None
        lpServiceStartName = wintypes.LPWSTR(account) if account is not None else None
        lpPassword = wintypes.LPWSTR(account_password) if account_password is not None else None

        assert self.handle is not None
        service_h = CreateService(self.handle, lpServiceName, lpDisplayName, dwDesiredAccess, dwServiceType,
                                  dwStartType, dwErrorControl, lpBinaryPathName, lpLoadOrderGroup, lpdwTagId,
                                  lpDependencies, lpServiceStartName, lpPassword)
        if service_h is None:
            raise ctypes.WinError()
        return Service(service_h)

    def open_service(self, name, access=ServiceAccess.ALL):
        service_h = OpenService(self.handle, wintypes.LPWSTR(name), access)
        if service_h is None:
            raise ctypes.WinError()
        return Service(service_h)

    def close(self):
        if self.handle is not None:
            if not CloseServiceHandle(self.handle):
                if ctypes.get_last_error() != ERROR_INVALID_HANDLE:
                    raise ctypes.WinError()
            self.handle = None

    def is_service_exist(self, name):
        try:
            service = self.open_service(name, ServiceAccess.QUERY_STATUS)
            service.close()
            return True
        except WindowsError:
            return False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
