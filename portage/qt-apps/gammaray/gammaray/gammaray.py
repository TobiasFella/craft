import info

class subinfo( info.infoclass ):
    def setTargets( self ):
        self.versionInfo.setDefaultValues()
        self.targetDigests['2.6.0'] = (['762fc1e61fb141462e72fe048b4a7bbf1063eea6a2209963c8aa1ad7696b0217'], CraftHash.HashAlgorithm.SHA256)

        self.shortDescription = "GammaRay is a tool to poke around in a Qt-application and also to manipulate the application to some extent"

    def setDependencies( self ):
        self.buildDependencies['virtual/base'] = 'default'
        self.dependencies["libs/qtbase"] = "default"
        self.dependencies['qt-apps/kdstatemachineeditor'] = 'default'

from Package.CMakePackageBase import *

class Package( CMakePackageBase ):
    def __init__( self ):
        CMakePackageBase.__init__( self )
        self.changePackager(NullsoftInstallerPackager)


    def createPackage(self):
        self.defines["productname"] = "GammaRay"
        self.defines["website"] = "http://www.kdab.com/gammaray"
        self.defines["executable"] = "bin\\gammaray.exe"
#            self.defines["icon"] = os.path.join(os.path.dirname(__file__), "kdevelop.ico")

        self.ignoredPackages.append("binary/mysql-pkg")

        return TypePackager.createPackage(self)

