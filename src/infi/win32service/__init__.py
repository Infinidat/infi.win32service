__import__("pkg_resources").declare_namespace(__name__)

from .utils import enum

from .service import SERVICE_STATUS, SERVICE_NOTIFY, Service, ServiceCtrl

from .service_control_manager import ServiceManagerAccess, SC_ACTIVE_DATABASE, ServiceType, ServiceStartType
from .service_control_manager import ServiceErrorControl, ServiceAccess
from .service_control_manager import ServiceControlManagerContext, ServiceControlManager

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
