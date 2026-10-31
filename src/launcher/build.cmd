@echo off
rem Builds launcher-ia32.exe and launcher-x64.exe (same 32-bit binary) into ..\..\build\
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars32.bat" >nul
cd /d "%~dp0"
if not exist ..\..\build mkdir ..\..\build
cl /nologo /O2 /MT /W3 /utf-8 /DUNICODE /D_UNICODE launcher.c /Fe:..\..\build\launcher-ia32.exe /Fo:..\..\build\ /link /SUBSYSTEM:WINDOWS user32.lib
copy /y ..\..\build\launcher-ia32.exe ..\..\build\launcher-x64.exe >nul
