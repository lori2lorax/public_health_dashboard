@echo off
where node >nul 2>nul
if %errorlevel% equ 0 (
  echo Starting EpiCentre with the installed Node.js runtime...
  node "%~dp0serve.mjs"
  exit /b %errorlevel%
)

set "CODEX_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if exist "%CODEX_NODE%" (
  echo Starting EpiCentre with the Codex Node.js runtime...
  "%CODEX_NODE%" "%~dp0serve.mjs"
  exit /b %errorlevel%
)

echo Node.js 18 or newer is required.
echo Download it from https://nodejs.org/ and run this launcher again.
pause
exit /b 1
