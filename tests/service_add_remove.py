from infi.win32service import ServiceControlManagerContext
from infi.win32service import ServiceType, ServiceStartType

INFI_SERVICE_NAME = u"InfinidatTest"

with ServiceControlManagerContext() as scm:
    scm.create_service(INFI_SERVICE_NAME,
                       u"Infinidat Test Service",
                       ServiceType.WIN32_OWN_PROCESS,
                       ServiceStartType.AUTO, 
                       u"\"c:\\home\\projects\\vendata\\win32service\\bin\\python.exe\" test.py /run")
