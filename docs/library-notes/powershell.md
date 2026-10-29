# powershell

**Kind:** language

**Version:** Windows PowerShell 5.1 (`powershell.exe`, ships with Windows 10 and 11) and `cmd.exe` batch files

**Docs:** https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1

## Best practices

- `-ExecutionPolicy Bypass` sets the policy for that process and its children only; the registry setting is untouched — [about_Execution_Policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1)
- `-File` must be the last parameter; everything after it is the script path and its arguments — [about_PowerShell_exe](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1)
- From a batch file, pass the script as `"%~dp0script.ps1"`; a relative `.\script.ps1` is resolved against the caller's directory and fails — [about_PowerShell_exe](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1)
- With `-File`, the process exit code is the script's `exit N`, `1` after a script-terminating error, else `0` — [about_Automatic_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-5.1)
- After a native command, read `$LASTEXITCODE`; end a script with `exit $LASTEXITCODE` to pass a native code on — [about_Automatic_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-5.1)
- `$PSScriptRoot` is the running script's folder (valid in every script since 3.0) — [about_Automatic_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-5.1)
- In a batch file, `exit /b N` ends the script (not `cmd.exe`) and sets `ERRORLEVEL` to `N` — [exit](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/exit)

## Pattern

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
set "SETUP_EXIT=%ERRORLEVEL%"
exit /b %SETUP_EXIT%
```

Follows [about_PowerShell_exe](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1) and [exit](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/exit).

## Traps

- `Restricted` is the default on Windows clients: no `.ps1` runs, only typed commands — [about_Execution_Policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1)
- A Group Policy execution policy wins over `-ExecutionPolicy` — [about_Execution_Policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1)
- `$ErrorActionPreference = 'Stop'` does not stop on a native command's non-zero exit code; check `$LASTEXITCODE` — [about_Automatic_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-5.1)
- Known 5.1 behaviour, not stated on its docs pages: when stderr is redirected, a native command's stderr lines (uv's progress) can become error records, which `Stop` turns into a failure; rely on `$LASTEXITCODE` instead
- `setlocal` saves and restores environment variables only, so the console code page `chcp` set stays after the script — [setlocal](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/setlocal)
- With `-File`, Ctrl+C exits with code `0` — [about_PowerShell_exe](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1)
- Windows PowerShell 5.1 reads a UTF-8 file without a BOM in the ANSI code page; keep scripts ASCII — [about_Character_Encoding](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding?view=powershell-5.1)
- uv's `install.ps1` refuses to run unless the effective policy is `Unrestricted`, `RemoteSigned` or `Bypass`, and ends with `exit` — run it in a child `powershell -ExecutionPolicy Bypass` — [install.ps1 0.13.6](https://astral.sh/uv/0.13.6/install.ps1)

## Sources

- [about_PowerShell_exe (5.1)](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1) — `-File`, `-ExecutionPolicy`, exit codes (accessed 2026-10-29)
- [about_Automatic_Variables (5.1)](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-5.1) — `$LASTEXITCODE`, `$PSScriptRoot`, `$?` (accessed 2026-10-29)
- [about_Execution_Policies (5.1)](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1) — policies, scopes, Group Policy precedence (accessed 2026-10-29)
- [exit](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/exit) — `exit /b` in batch files (accessed 2026-10-29)
- [setlocal](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/setlocal) — what `endlocal` restores (accessed 2026-10-29)
- [install.ps1 0.13.6](https://astral.sh/uv/0.13.6/install.ps1) — install dir order, policy check, `exit 1` (accessed 2026-10-29)
