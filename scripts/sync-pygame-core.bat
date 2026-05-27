@echo off
REM Fetch latest pygame_core from origin/main (.gitmodules pins branch=main, update=merge)
REM and stage the new submodule pointer. Run 'git commit && git push' afterward to publish.
cd /d "%~dp0.."
git submodule update --remote --merge src/pygame_core
git add src/pygame_core
pause
