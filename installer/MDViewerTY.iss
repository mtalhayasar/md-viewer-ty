; MD Viewer TY — Inno Setup 6 kurulum betiği
; Derleme: python tools/build.py  (ya da: iscc /DAppVersion=1.0.0 installer\MDViewerTY.iss)

#define AppName "MD Viewer TY"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppExe "MDViewerTY.exe"
#define AppPublisher "Talha Yaşar"
#define AppUrl "https://github.com/mtalhayasar/md-viewer-ty"
#define ProgId "MDViewerTY.Markdown"
#define CapKey "Software\MDViewerTY\Capabilities"

[Setup]
; AppId kurulumun kimliğidir; güncellemelerin aynı kurulumun üstüne yazması için ASLA değiştirme.
AppId={{3105FA5E-B5A5-4B8F-B4EB-AA21CA04B05B}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}/issues
AppUpdatesURL={#AppUrl}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
; Varsayılan: yönetici izni istemeden yalnızca bu kullanıcıya kur; isteyen tüm kullanıcılar için seçebilir.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\dist
OutputBaseFilename=MDViewerTY-Setup-{#AppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile=..\LICENSE
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
ChangesAssociations=yes
CloseApplications=yes
RestartApplications=no
UsePreviousTasks=yes
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Kurulumu

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
turkish.AssocGroup=Varsayılan program
english.AssocGroup=Default app
turkish.AssocTask=.md dosyaları MD Viewer TY ile açılsın (varsayılan program yap)
english.AssocTask=Open .md files with MD Viewer TY (make it the default app)
turkish.FileTypeName=Markdown Belgesi
english.FileTypeName=Markdown Document
turkish.AppDescription=Okuma odaklı Markdown görüntüleyici
english.AppDescription=Reading-focused Markdown viewer
turkish.ConfirmDefaults=Windows, varsayılan uygulama değişikliğini senin onaylamanı istiyor.%n%nŞu an .md dosyaları başka bir programla açılıyor. Ayarlar açılsın mı? Açılan pencerede .md için "MD Viewer TY"yi seçmen yeterli.
english.ConfirmDefaults=Windows requires you to confirm default app changes.%n%n.md files currently open with another program. Open Settings now? Just pick "MD Viewer TY" for .md there.
turkish.WebView2Missing=MD Viewer TY, Microsoft Edge WebView2 Runtime'a ihtiyaç duyar ve bu bilgisayarda bulunamadı.%n%nİndirme sayfası açılsın mı? (Kurulum devam edecek; uygulamayı WebView2 kurulduktan sonra açabilirsin.)
english.WebView2Missing=MD Viewer TY requires the Microsoft Edge WebView2 Runtime, which was not found.%n%nOpen the download page? (Setup will continue; run the app after installing WebView2.)

[Tasks]
Name: "assoc"; Description: "{cm:AssocTask}"; GroupDescription: "{cm:AssocGroup}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\MDViewerTY\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\md-file.ico"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; Eski sürümden kalan kütüphaneler yeni sürümle çakışmasın.
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "TalhaYasar.MDViewerTY"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; --- Dosya türü (ProgID) ---
Root: HKA; Subkey: "Software\Classes\{#ProgId}"; ValueType: string; ValueName: ""; ValueData: "{cm:FileTypeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#ProgId}"; ValueType: string; ValueName: "FriendlyTypeName"; ValueData: "{cm:FileTypeName}"
Root: HKA; Subkey: "Software\Classes\{#ProgId}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\md-file.ico"
Root: HKA; Subkey: "Software\Classes\{#ProgId}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""

; --- "Birlikte aç" listesinde her zaman görünsün ---
Root: HKA; Subkey: "Software\Classes\.md\OpenWithProgids"; ValueType: string; ValueName: "{#ProgId}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.markdown\OpenWithProgids"; ValueType: string; ValueName: "{#ProgId}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mdown\OpenWithProgids"; ValueType: string; ValueName: "{#ProgId}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\.mkd\OpenWithProgids"; ValueType: string; ValueName: "{#ProgId}"; ValueData: ""; Flags: uninsdeletevalue

Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".md"; ValueData: ""
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".markdown"; ValueData: ""
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""

; --- Windows "Varsayılan uygulamalar" listesine kayıt ---
Root: HKA; Subkey: "Software\MDViewerTY"; Flags: uninsdeletekey
Root: HKA; Subkey: "{#CapKey}"; ValueType: string; ValueName: "ApplicationName"; ValueData: "{#AppName}"
Root: HKA; Subkey: "{#CapKey}"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "{cm:AppDescription}"
Root: HKA; Subkey: "{#CapKey}"; ValueType: string; ValueName: "ApplicationIcon"; ValueData: "{app}\{#AppExe},0"
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".md"; ValueData: "{#ProgId}"
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".markdown"; ValueData: "{#ProgId}"
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mdown"; ValueData: "{#ProgId}"
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mkd"; ValueData: "{#ProgId}"
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "{#AppName}"; ValueData: "{#CapKey}"; Flags: uninsdeletevalue

; --- Kullanıcı "varsayılan program yap" dediyse ---
Root: HKA; Subkey: "Software\Classes\.md"; ValueType: string; ValueName: ""; ValueData: "{#ProgId}"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.markdown"; ValueType: string; ValueName: ""; ValueData: "{#ProgId}"; Tasks: assoc

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; Uygulama içinden yapılan güncellemeden sonra uygulamayı yeniden aç.
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: IsAppUpdate

[Code]
const
  WebView2Guid = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function IsAppUpdate: Boolean;
begin
  Result := ExpandConstant('{param:UPDATE|0}') = '1';
end;

function HasWebView2: Boolean;
var
  V: String;
begin
  Result :=
    (RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\' + WebView2Guid, 'pv', V) and (V <> '') and (V <> '0.0.0.0')) or
    (RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\' + WebView2Guid, 'pv', V) and (V <> '') and (V <> '0.0.0.0')) or
    (RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\' + WebView2Guid, 'pv', V) and (V <> '') and (V <> '0.0.0.0'));
end;

function InitializeSetup: Boolean;
var
  Code: Integer;
begin
  Result := True;
  if not WizardSilent and not HasWebView2 then
    if MsgBox(CustomMessage('WebView2Missing'), mbConfirmation, MB_YESNO) = IDYES then
      ShellExec('open', 'https://go.microsoft.com/fwlink/p/?LinkId=2124703', '', '', SW_SHOWNORMAL, ewNoWait, Code);
end;

{ Kullanıcı daha önce .md için başka bir program seçtiyse Windows bu seçimi (UserChoice) korur;
  kayıt defteri tek başına yetmez, kullanıcının Ayarlar'dan onaylaması gerekir. }
function UserChoiceIsOther(const Ext: String): Boolean;
var
  ProgId: String;
  Base: String;
begin
  Base := 'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\' + Ext;
  Result := False;
  if RegQueryStringValue(HKCU, Base + '\UserChoiceLatest\ProgId', 'ProgId', ProgId) or
     RegQueryStringValue(HKCU, Base + '\UserChoice', 'ProgId', ProgId) then
    Result := (ProgId <> '') and (CompareText(ProgId, '{#ProgId}') <> 0);
end;

{ [Code] içinde HKA her durumda doğru köke çözülmediği için kökü açıkça seç. }
function AppRoot: Integer;
begin
  if IsAdminInstallMode then
    Result := HKLM
  else
    Result := HKCU;
end;

{ "Varsayılan yap" seçildiğinde önceki varsayılanı sakla; kaldırırken geri yükle. }
procedure SavePreviousDefault(const Ext: String);
var
  V, Saved: String;
begin
  if RegQueryStringValue(AppRoot, 'Software\MDViewerTY\PreviousDefaults', Ext, Saved) then
    exit;
  if not RegQueryStringValue(AppRoot, 'Software\Classes\' + Ext, '', V) then
    V := '';
  if CompareText(V, '{#ProgId}') <> 0 then
    RegWriteStringValue(AppRoot, 'Software\MDViewerTY\PreviousDefaults', Ext, V);
end;

procedure RestorePreviousDefault(const Ext: String);
var
  V, Prev: String;
begin
  if not (RegQueryStringValue(AppRoot, 'Software\Classes\' + Ext, '', V) and (CompareText(V, '{#ProgId}') = 0)) then
    exit;
  if RegQueryStringValue(AppRoot, 'Software\MDViewerTY\PreviousDefaults', Ext, Prev) and (Prev <> '') then
    RegWriteStringValue(AppRoot, 'Software\Classes\' + Ext, '', Prev)
  else
    RegDeleteValue(AppRoot, 'Software\Classes\' + Ext, '');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  { usUninstall: kayıt defteri girdileri silinmeden önce çalışır. }
  if CurUninstallStep = usUninstall then
  begin
    RestorePreviousDefault('.md');
    RestorePreviousDefault('.markdown');
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
  Url: String;
begin
  if (CurStep = ssInstall) and WizardIsTaskSelected('assoc') then
  begin
    SavePreviousDefault('.md');
    SavePreviousDefault('.markdown');
  end;
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('assoc') and not WizardSilent and UserChoiceIsOther('.md') then
  begin
    if IsAdminInstallMode then
      Url := 'ms-settings:defaultapps?registeredAppMachine=MD%20Viewer%20TY'
    else
      Url := 'ms-settings:defaultapps?registeredAppUser=MD%20Viewer%20TY';
    if MsgBox(CustomMessage('ConfirmDefaults'), mbConfirmation, MB_YESNO) = IDYES then
      ShellExec('open', Url, '', '', SW_SHOWNORMAL, ewNoWait, Code);
  end;
end;
