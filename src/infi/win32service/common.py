from .utils import enum

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

# From http://msdn.microsoft.com/en-us/library/windows/desktop/ms682450%28v=vs.85%29.aspx
# Also, from http://msdn.microsoft.com/en-us/library/windows/desktop/ms685996%28v=vs.85%29.aspx
# -- CreateService.dwServiceType and SERVICE_STATUS structure used in SetServiceStatus (but only a subset is available
#    there):
ServiceType = enum(
    KERNEL_DRIVER         = 0x00000001,
    FILE_SYSTEM_DRIVER    = 0x00000002,
    ADAPTER               = 0x00000004,
    RECOGNIZER_DRIVER     = 0x00000008,
    WIN32_OWN_PROCESS     = 0x00000010,
    WIN32_SHARE_PROCESS   = 0x00000020,
    INTERACTIVE_PROCESS   = 0x00000100)

ERROR_INVALID_HANDLE = 6
