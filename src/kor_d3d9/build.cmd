@echo off
rem Builds d3d9.dll (x86) into ..\..\build\
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars32.bat" >nul
cd /d "%~dp0"
if not exist ..\..\build mkdir ..\..\build
cl /nologo /O2 /MT /EHsc /W3 /LD main.cpp /Fe:..\..\build\d3d9.dll /Fo:..\..\build\ /link /DEF:d3d9.def user32.lib gdi32.lib
