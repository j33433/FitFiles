;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "FitFiles"
  OutFile "Install FitFiles.exe"

  ;Default installation folder
  InstallDir "$LOCALAPPDATA\FitFiles"

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\FitFiles" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user

  ; Tried them all and this was best
  SetCompressor /SOLID lzma
  
;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING
  !define MUI_ICON "..\images\FitFiles.ico"

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  ;!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "FitFiles" SecDummy
  SetOutPath "$INSTDIR"
  File /r "..\dist\fitfileanalyses\*"

	
  WriteRegStr HKCU "Software\FitFiles" "" $INSTDIR

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  CreateDirectory "$SMPROGRAMS\FitFiles"
  CreateShortCut "$SMPROGRAMS\FitFiles\FitFiles.lnk" "$INSTDIR\fitfileanalyses.exe" ""
  CreateShortCut "$SMPROGRAMS\FitFiles\Uninstall FitFiles.lnk" "$INSTDIR\Uninstall.exe" ""
  CreateShortCut "$DESKTOP\FitFiles.lnk" "$INSTDIR\fitfileanalyses.exe" ""
SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecDummy ${LANG_ENGLISH} "FitFiles"

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$SMPROGRAMS\FitFiles\FitFiles.lnk"
  Delete "$SMPROGRAMS\FitFiles\Uninstall FitFiles.lnk"
  RMDir "$SMPROGRAMS\FitFiles"
  Delete "$DESKTOP\FitFiles.lnk"
  
  RMDir /r "$INSTDIR\FitFiles"
  RMDir "$INSTDIR"

  DeleteRegKey /ifempty HKCU "Software\FitFiles"
SectionEnd
