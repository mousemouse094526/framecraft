@echo off
rem framecraft setup for Windows. Runs setup.ps1 even where the execution
rem policy is Restricted, in a UTF-8 console so the Thai output reads right.
setlocal
rem "Active code page: 874." -> 874, to give the console back as it was.
for /f "tokens=2 delims=:" %%p in ('chcp') do set "OLD_CP=%%p"
if defined OLD_CP set "OLD_CP=%OLD_CP: =%"
if defined OLD_CP set "OLD_CP=%OLD_CP:.=%"
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
set "SETUP_EXIT=%ERRORLEVEL%"
rem A double-click runs "cmd.exe /c ...", and that window would close before
rem the checklist is read. Quotes are dropped so the comparison can't break.
set "CMD_LINE=%cmdcmdline:"=%"
if /i not "%CMD_LINE: /c =%"=="%CMD_LINE%" pause
if defined OLD_CP chcp %OLD_CP% >nul
exit /b %SETUP_EXIT%
