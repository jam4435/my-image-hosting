@echo off
setlocal

cd /d "%~dp0"

echo Repo: %CD%
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git was not found in PATH.
  pause
  exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo [ERROR] This folder is not a Git repository.
  pause
  exit /b 1
)

echo [1/3] git add .
git add .
if errorlevel 1 goto :fail

echo.
echo [2/3] git commit -m "update"
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "update"
  if errorlevel 1 goto :fail
) else (
  echo No staged changes. Skipping commit.
)

echo.
echo [3/3] git push
git push
if errorlevel 1 goto :fail

echo.
echo Done.
pause
exit /b 0

:fail
echo.
echo Failed. See messages above.
pause
exit /b 1
