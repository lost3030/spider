@echo off
cd /d "%~dp0.."
"C:\Program Files\Docker\Docker\resources\bin\docker.exe" run --rm mofcom-watch:latest
