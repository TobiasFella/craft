import info
from Package.CMakePackageBase import *

class subinfo( info.infoclass ):
    def setTargets( self ):
        for ver in [ '8.39' ]:
            self.targets[ ver ] = 'ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-' + ver + '.tar.bz2'
            self.targetInstSrc[ ver ] = 'pcre-' + ver
        self.patchToApply[ '8.39' ] = [ ( "pcre-8.10-20101125.diff", 1 ) ]

        self.targetDigests['8.39'] = '5e38289fd1b4ef3e8426f31a01e34b6924d80b90'

        self.shortDescription = "Perl-Compatible Regular Expressions"
        self.defaultTarget = '8.39'

    def setDependencies( self ):
        self.buildDependencies[ 'virtual/base' ] = 'default'
        self.dependencies[ 'win32libs/libbzip2' ] = 'default'
        self.dependencies[ 'win32libs/zlib' ] = 'default'


class Package( CMakePackageBase ):
    def __init__( self, **args ):
        CMakePackageBase.__init__( self )

        defines  = "-DBUILD_SHARED_LIBS=ON "
        defines += "-DPCRE_SUPPORT_UNICODE_PROPERTIES=ON "
        defines += "-DPCRE_SUPPORT_UTF8=ON "
        defines += "-DPCRE_EBCDIC=OFF "
        self.subinfo.options.configure.defines = defines

