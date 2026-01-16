@echo off
REM Minimal make.bat for Sphinx documentation
REM You can set these variables from the command line.

REM Set default variables
set SPHINXOPTS=
set SPHINXBUILD=sphinx-build
set SPHINXPROJ=UltraPlot
set SOURCEDIR=.
set BUILDDIR=_build

REM Check if no arguments were provided (show help)
if "%1"=="" goto help

REM Route to the appropriate target
if "%1"=="help" goto help
if "%1"=="clean" goto clean

REM Catch-all target: route all unknown targets to Sphinx
goto catchall


:help
REM Put it first so that "make" without argument is like "make help".
%SPHINXBUILD% -M help "%SOURCEDIR%" "%BUILDDIR%" %SPHINXOPTS%
goto :eof


:clean
REM Make clean ignore .git folder
REM The /q doesn't raise error when files/folders not found
if exist api\ rmdir /s /q api\
if exist "%BUILDDIR%\html\" rmdir /s /q "%BUILDDIR%\html\"
if exist "%BUILDDIR%\doctrees\" rmdir /s /q "%BUILDDIR%\doctrees\"
goto :eof


:catchall
REM Route target to Sphinx using the "make mode" option
%SPHINXBUILD% -M %1 "%SOURCEDIR%" "%BUILDDIR%" %SPHINXOPTS%
goto :eof