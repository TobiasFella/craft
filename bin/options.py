## @package property handling
#
# (c) copyright 2009-2011 Ralf Habacker <ralf.habacker@freenet.de>
#
#
#
import utils
from CraftConfig import *
from CraftCore import CraftCore
from Blueprints.CraftPackageObject import *
from CraftDebug import deprecated

import configparser
import atexit
import copy

class UserOptions(object):
    class UserOptionsSingleton(object):
        _instance = None

        @property
        def __coreCategory(self):
            return "#Core"

        @property
        def __header(self):
            return """\
# The content of this file is partly autogenerated
# You can modify values and add settings for your blueprints
# Common settings available for all blueprints are:
#     ignored: [True|False]
#     version: some version
#     # use the same url as defined for the target but checks out a different branch
#     branch: str
#     patchLevel: int
#     buildTests: [True|False]
#     # arguments passed to the configure step
#     args: str
#
# Example:
##     [libs]
##     ignored = True
##
##     [lib/qt5]
##     version = 5.9.3
##     ignored = False
##     withMySQL = True
##
##     [kde/pim/akonadi]
##     args = -DAKONADI_BUILD_QSQLITE=On
##
#
# Settings are inherited, so you can set them for a whole sub branch or a single blueprint.
# While blueprint from [libs] are all ignored blueprint from [libs/qt5] are not.
#
"""

        def __init__(self):
            self.cachedOptions = {}
            self.commandlineOptions = {}
            self.packageOptions = {}
            self.options = {}
            self.registeredOptions = {}

            self.path = CraftCore.settings.get("Blueprints", "Settings",
                                               os.path.join(CraftCore.standardDirs.etcDir(), "BlueprintSettings.ini"))
            self.settings = configparser.ConfigParser(allow_no_value=True)
            self.settings.optionxform = str

            if os.path.isfile(self.path):
                self.settings.read(self.path)
            if not self.settings.has_section(self.__coreCategory):
                self.settings.add_section(self.__coreCategory)

            self.options = Options(package=None)

            settings = self.settings[self.__coreCategory]
            self._init_vars(settings, self.options)


        def initPackage(self, option):
            path = option._package.path
            if not self.settings.has_section(path):
                self.settings.add_section(path)
            settings = self.settings[path]
            return settings

        def toBool(self, x : str) -> bool:
            if not x:
                return False
            return self.settings._convert_to_boolean(x)

        def _init_vars(self, settings, opt, prefix="") -> None:
            for var in vars(opt):
                if var.startswith("_"):
                    continue
                attr = getattr(opt, var)
                if isinstance(attr, (bool, str, int, type(None))):
                    key = f"{prefix}{var}"
                    if key not in settings:
                        if not attr is None:
                            settings[key] = str(attr)
                        else:
                            settings[key] = None
                    else:
                        val = settings[key]
                        if isinstance(attr, bool):
                            val = self.toBool(val)
                        setattr(opt, var, val)
                else:
                    self._init_vars(settings, attr, prefix=f"{prefix}{var}.")

        @staticmethod
        @atexit.register
        def __dump():
            instance = UserOptions.UserOptionsSingleton._instance
            if instance:
                try:
                    with open(instance.path, 'wt+') as configfile:
                        print(instance.__header, file=configfile)
                        instance.settings.write(configfile)
                except:
                    CraftCore.log.debug(f"Failed so save {instance.path}")


    @staticmethod
    def instance():
        if not UserOptions.UserOptionsSingleton._instance:
                UserOptions.UserOptionsSingleton._instance = UserOptions.UserOptionsSingleton()
        return UserOptions.UserOptionsSingleton._instance


    def __init__(self, package):
        self._cachedFromParent = {}
        self._package = package

        _register  = self.registerOption
        _convert = self._convert

        _register("version",    str,    permanent=False)
        _register("branch",     str,    permanent=False)
        _register("patchLevel", int,    permanent=False)
        _register("ignored",    bool,   permanent=False)
        _register("buildTests", bool,   permanent=False)
        _register("args",       "",     permanent=False)

        settings = UserOptions.instance().settings
        if settings.has_section(package.path):
            _registered = UserOptions.instance().registeredOptions[package.path]
            for k, v in settings[package.path].items():
                if k in _registered:
                    v = _convert(_registered[k], v)
                setattr(self, k, v)
    @staticmethod
    def get(package):
        _instance = UserOptions.instance()
        packagePath = package.path
        if packagePath in _instance.cachedOptions:
            option = _instance.cachedOptions[packagePath]
        else:
            option = UserOptions(package)
            _instance.cachedOptions[packagePath] = option
        return option

    def _convert(self, valA, valB):
        """
        Converts valB to type(valA)
        """
        try:
            if valA is None:
                return valB
            _type = valA if callable(valA) else type(valA)
            if _type == type(valB):
                return valB
            if _type is bool:
                return UserOptions.instance().toBool(valB)
            return _type(valB)
        except Exception as e:
            CraftCore.log.error(f"Can't convert {valB} to {_type.__name__}")
            raise e



    @staticmethod
    def setOptions(optionsIn):
        options = {}
        packageOptions = {}
        for o in optionsIn:
            key, value = o.split("=", 1)
            key, value = key.strip(), value.strip()
            if "." in key:
                package, key = key.split(".", 1)
                if package == "dynamic":
                    CraftCore.log.warning(f"Detected a deprecated setting \"{package}.{key} = {value}\", use the BlueprintsSettings.ini")
                    options[key] = value
                else:
                    if "/" in package:
                        # make sure it is a blueprint related setting
                        if CraftPackageObject.get(package):
                            if package not in packageOptions:
                                 packageOptions[package] = {}
                            packageOptions[package][key] = value
                        elif not CraftPackageObject.bootstrapping():
                            # in case we are bootstrapping Craft, we might not know that package yet
                            raise BlueprintNotFoundException(package, f"Package {package} not found, failed to set option {key} = {value}")
                    else:
                        options[f"{package}.{key}"] = value
        UserOptions.instance().commandlineOptions = options
        UserOptions.instance().packageOptions = packageOptions


    @staticmethod
    def addPackageOption(package : CraftPackageObject, key : str, value : str) -> None:
        if package.path not in UserOptions.instance().packageOptions:
            UserOptions.instance().packageOptions[package.path] = {}
        UserOptions.instance().packageOptions[package.path][key] = value


    def setOption(self, key, value) -> bool:
        _instance = UserOptions.instance()
        package = self._package
        if package.path not in _instance.registeredOptions:# actually that can only happen if package is invalid
            CraftCore.log.error(f"{package} has no options")
            return False
        if key not in _instance.registeredOptions[package.path]:
            CraftCore.log.error(f"{package} unknown option {key}")
            CraftCore.log.error(f"Valid options are")
            for opt, default in _instance.registeredOptions[package.path].items():
                default = default if callable(default) else type(default)
                CraftCore.log.error(f"\t{default.__name__} : {opt}")
            return False
        value = self._convert(_instance.registeredOptions[package.path][key], value)
        settings = _instance.initPackage(self)
        settings[key] = str(value)
        setattr(self, key, value)
        return True

    def registerOption(self, key : str, default, permanent=True) -> bool:
        _instance = UserOptions.instance()
        package = self._package
        if package.path not in _instance.registeredOptions:
            _instance.registeredOptions[package.path] = {}
        if key in _instance.registeredOptions[package.path]:
            raise BlueprintException(f"Failed to register option:\n[{package}]\n{key}={default}\nThe setting {key} is already registered.", package)
            return False
        _instance.registeredOptions[package.path][key] = default
        if permanent:
            settings = _instance.initPackage(self)
            if key and key not in settings:
                settings[key] = str(default)

        # don't try to save types
        if not callable(default):
            if not hasattr(self, key):
                setattr(self, key, default)
            else:
                # convert type
                old = getattr(self, key)
                try:
                    new = self._convert(default, old)
                except:
                    raise BlueprintException(f"Found an invalid option in BlueprintSettings.ini,\n[{self._package}]\n{key}={old}", self._package)
                #print(key, type(old), old, type(new), new)
                setattr(self, key, new)
        return True

    def __getattribute__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        try:
            member = super().__getattribute__(name)
        except AttributeError:
            member = None
        if member and callable(member):
            return member

        #check cache
        _cache = super().__getattribute__("_cachedFromParent")
        if not member and name in _cache:
            return _cache[name]

        out = None
        _instance = UserOptions.instance()
        _package = super().__getattribute__("_package")
        _packagePath = _package.path
        if _packagePath in _instance.packageOptions and name in _instance.packageOptions[_packagePath]:
            if _packagePath not in _instance.registeredOptions or name not in _instance.registeredOptions[_packagePath]:
                 raise BlueprintException(f"Package {_package} has no registered option {name}", _package)
            out = self._convert(_instance.registeredOptions[_packagePath][name], _instance.packageOptions[_packagePath][name])
        elif name in _instance.commandlineOptions:
            # legacy option, removee soon
            out = _instance.commandlineOptions[name]
            CraftCore.log.warning(f"Deprecated use of options without package, please specify the package for the option {name}:\n"
                                  f"{_packagePath}.{name}={out}")
        elif member is not None:
            # value is not overwritten by comand line options
            return member
        else:
            parent = _package.parent
            if parent:
                out = getattr(UserOptions.get(parent), name)

        if not out:
            # name is a registered option and not a type but a default value
            if _packagePath in _instance.registeredOptions and name in _instance.registeredOptions[_packagePath]:
                default = _instance.registeredOptions[_packagePath][name]
                if not callable(default):
                    out = default


        # skip lookup in command line options and parent objects the enxt time
        _cache[name] = out
        #print(_packagePath, name, type(out), out)
        return out

class OptionsBase(object):
    def __init__(self):
        pass

## options for the fetch action
class OptionsFetch(OptionsBase):
    def __init__(self):
        ## option comment
        self.option = None
        self.ignoreExternals = False
        ## enable submodule support in git single branch mode
        self.checkoutSubmodules = False


## options for the unpack action
class OptionsUnpack(OptionsBase):
    def __init__(self):
        #  Use this option to run 3rd party installers
        self.runInstaller = False


## options for the configure action
class OptionsConfigure(OptionsBase):
    def __init__(self):
        ## with this option additional arguments could be added to the configure commmand line
        self.args = None
        ## with this option additional arguments could be added to the configure commmand line (for static builds)
        self.staticArgs = None
        ## set source subdirectory as source root for the configuration tool.
        # Sometimes it is required to take a subdirectory from the source tree as source root
        # directory for the configure tool, which could be enabled by this option. The value of
        # this option is added to sourceDir() and the result is used as source root directory.
        self.configurePath = None

        # add the cmake defines that are needed to build tests here
        self.testDefine = None

        ## run autogen in autotools
        self.bootstrap = False

        # do not use default include path
        self.noDefaultInclude = False

        ## do not use default lib path
        self.noDefaultLib = False

        ## set this attribute in case a non standard configuration
        # tool is required (supported currently by QMakeBuildSystem only)
        self.tool = False

        # cflags currently only used for autotools
        self.cflags = ""

        # cxxflags currently only used for autotools
        self.cxxflags = ""

        # ldflags currently only used for autotools
        self.ldflags = ""

        # the project file, this is either a .pro for qmake or a sln for msbuild
        self.projectFile = None

        # whether to not pass --datarootdir configure
        self.noDataRootDir = False


## options for the make action
class OptionsMake(OptionsBase):
    def __init__(self):
        ## ignore make error
        self.ignoreErrors = None
        ## options for the make tool
        self.args = ""
        self.supportsMultijob = True
        
    @property
    @deprecated("options.make.args")
    def makeOptions(self):
        return self.args
    
    @makeOptions.setter
    @deprecated("options.make.args")
    def makeOptions(self, x):
        self.args = x
        
class OptionsInstall(OptionsBase):
    def __init__(self):
        ## options passed to make on install
        self.args = "install"

## options for the package action
class OptionsPackage(OptionsBase):
    def __init__(self):
        ## defines the package name
        self.packageName = None
        ## defines the package version
        self.version = None
        ## use compiler in package name
        self.withCompiler = True
        ## use special packaging mode  (only for qt)
        self.specialMode = False
        ## pack also sources
        self.packSources = True
        ## pack from subdir of imageDir()
        # currently supported by SevenZipPackager
        self.packageFromSubDir = None
        ## use architecture in package name
        # currently supported by SevenZipPackager
        self.withArchitecture = False
        ## add file digests to the package located in the manifest sub dir
        # currently supported by SevenZipPackager
        self.withDigests = True
        ##disable stripping of binary files
        # needed for mysql, striping make the library unusable
        self.disableStriping = False

        ##disable the binary cache for this package
        self.disableBinaryCache = False

        ## wheter to move the plugins to bin
        self.movePluginsToBin = utils.OsUtils.isWin()

class OptionsGit(OptionsBase):
    def __init__(self):
        ## enable support for applying patches in 'format-patch' style with 'git am' (experimental support)
        self.enableFormattedPatch = False


## main option class
class Options(object):
    def __init__(self, package=None):
        if package:
            self.__dict__ = copy.deepcopy(UserOptions.instance().options.__dict__)
            self.dynamic = UserOptions.get(package)
            self.configure.args = self.dynamic.args
            return

        ## options of the fetch action
        self.fetch = OptionsFetch()
        ## options of the unpack action
        self.unpack = OptionsUnpack()
        ## options of the configure action
        self.configure = OptionsConfigure()
        self.make = OptionsMake()
        self.install = OptionsInstall()
        ## options of the package action
        self.package = OptionsPackage()
        ## options of the git module
        self.git = OptionsGit()

        ## add the date to the target
        self.dailyUpdate = False

        ## has an issue with a too long path
        #enable by default for the ci
        # only applies for windows and if
        # [ShortPath]
        # EnableJunctions  = True
        self.needsShortPath = CraftCore.settings.getboolean("ContinuousIntegration", "Enabled", False)

        ## there is a special option available already
        self.buildTools = False
        self.buildStatic = CraftCore.settings.getboolean("Compile", "Static")

        self.useShadowBuild = True

    def isActive(self, package):
        if isinstance(package, str):
            package = CraftPackageObject.get(package)
        return not package.isIgnored()
