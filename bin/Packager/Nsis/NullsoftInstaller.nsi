; Copyright 2010 Patrick Spendrin <ps_ml@gmx.de>
; Copyright 2016 Kevin Funk <kfunk@kde.org>
; Copyright Hannah von Reth <vonreth@kde.org>
;
; Redistribution and use in source and binary forms, with or without
; modification, are permitted provided that the following conditions
; are met:
; 1. Redistributions of source code must retain the above copyright
;    notice, this list of conditions and the following disclaimer.
; 2. Redistributions in binary form must reproduce the above copyright
;    notice, this list of conditions and the following disclaimer in the
;    documentation and/or other materials provided with the distribution.
;
; THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
; ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
; IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
; ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
; FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
; DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
; OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
; HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
; LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
; OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
; SUCH DAMAGE.

; registry stuff
!define regkey "Software\@{company}\@{productname}"
!define uninstkey "Software\Microsoft\Windows\CurrentVersion\Uninstall\@{productname}"

BrandingText "Generated by Craft https://community.kde.org/Craft"

;--------------------------------

XPStyle on
ManifestDPIAware true


Name "@{productname}"
Caption "@{productname} @{version}"

OutFile "@{setupname}"

!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY "${regkey}"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME "Install_Mode"
!define MULTIUSER_INSTALLMODE_INSTDIR "@{productname}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY "${regkey}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUENAME "Install_Dir"

;Start Menu Folder Page Configuration
Var StartMenuFolder
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "SHCTX"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${regkey}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"

;!define MULTIUSER_USE_PROGRAMFILES64
@{multiuser_use_programfiles64}
;!define MULTIUSER_USE_PROGRAMFILES64

@{nsis_include_internal}
@{nsis_include}

!include "MultiUser.nsh"
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!include "process.nsh"


;!define MUI_ICON
@{installerIcon}
;!define MUI_ICON

!insertmacro MUI_PAGE_WELCOME

;!insertmacro MUI_PAGE_LICENSE
@{license}
;!insertmacro MUI_PAGE_LICENSE

!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!define MUI_COMPONENTSPAGE_NODESC
;!insertmacro MUI_PAGE_COMPONENTS
@{sections_page}
;!insertmacro MUI_PAGE_COMPONENTS

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_FINISHPAGE_LINK "Visit project homepage"
!define MUI_FINISHPAGE_LINK_LOCATION "@{website}"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

SetDateSave on
SetDatablockOptimize on
CRCCheck on
SilentInstall normal

Function .onInit
    !insertmacro MULTIUSER_INIT
    !if "@{architecture}" == "x64"
        ${IfNot} ${RunningX64}
            MessageBox MB_OK|MB_ICONEXCLAMATION "This installer can only be run on 64-bit Windows."
            Abort
        ${EndIf}
    !endif
FunctionEnd

Function un.onInit
    !insertmacro MULTIUSER_UNINIT
FunctionEnd

;--------------------------------

AutoCloseWindow false


; beginning (invisible) section
Section
  !insertmacro EndProcessWithDialog
  ExecWait '"$MultiUser.InstDir\uninstall.exe" /S _?=$MultiUser.InstDir'
  @{preInstallHook}
  WriteRegStr SHCTX "${regkey}" "Install_Dir" "$INSTDIR"
  WriteRegStr SHCTX "${MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY}" "${MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME}" "$MultiUser.InstallMode"
  ; write uninstall strings
  WriteRegStr SHCTX "${uninstkey}" "DisplayName" "@{productname}"
  WriteRegStr SHCTX "${uninstkey}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr SHCTX "${uninstkey}" "DisplayIcon" "$INSTDIR\@{iconname}"
  WriteRegStr SHCTX "${uninstkey}" "URLInfoAbout" "@{website}"
  WriteRegStr SHCTX "${uninstkey}" "Publisher" "@{company}"
  WriteRegStr SHCTX "${uninstkey}" "DisplayVersion" "@{version}"
  WriteRegDWORD SHCTX "${uninstkey}" "EstimatedSize" "@{estimated_size}"

  @{registy_hook}

  SetOutPath $INSTDIR


; package all files, recursively, preserving attributes
; assume files are in the correct places

File /a "@{dataPath}"
File /a "@{7za}"
File /a "@{icon}"
nsExec::ExecToLog '"$INSTDIR\7za.exe" x -r -y "$INSTDIR\@{dataName}" -o"$INSTDIR"'
Delete "$INSTDIR\7za.exe"
Delete "$INSTDIR\@{dataName}"

AddSize @{installSize}

WriteUninstaller "uninstall.exe"

SectionEnd

; create shortcuts
@{shortcuts}

;  allow to define additional sections
@{sections}


; Uninstaller
; All section names prefixed by "Un" will be in the uninstaller

UninstallText "This will uninstall @{productname}."

Section "Uninstall"
!insertmacro EndProcessWithDialog

DeleteRegKey SHCTX "${uninstkey}"
DeleteRegKey SHCTX "${regkey}"

!insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
RMDir /r "$SMPROGRAMS\$StartMenuFolder"

@{uninstallFiles}
@{uninstallDirs}

SectionEnd

;  allow to define additional Un.sections
@{un_sections}