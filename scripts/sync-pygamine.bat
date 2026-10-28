@echo off
REM Puts src/pygamine on the exact engine commit this project pins (the
REM submodule pointer in this repo). Run it after a pull or a branch switch,
REM or whenever the engine folder looks out of step. It never moves the pin
REM and never changes what this repo has committed. It does check out the
REM pinned commit inside src/pygamine (no branch): push or branch any engine
REM commits made there first. If the engine folder has uncommitted changes
REM that clash with the pin, git refuses and this says so.
cd /d "%~dp0.."
git submodule sync src/pygamine
git submodule update --init src/pygamine
if errorlevel 1 (
    echo.
    echo FAILED: src/pygamine is NOT on the pinned commit. See the git error above.
) else (
    echo.
    echo OK: src/pygamine is on the pinned commit.
)
pause

REM ---------------------------------------------------------------------------
REM Moving the pin to a newer engine (main is protected, so it goes by PR):
REM   1. Change pygamine itself in a PR there; for a release, a "Release x.y.z"
REM      PR and then the vx.y.z tag.
REM   2. In this project, on a new branch:
REM        cd src/pygamine
REM        git fetch --tags
REM        git checkout vx.y.z
REM        cd ../..
REM        git add src/pygamine
REM        git commit -m "Bump pygamine to vx.y.z"
REM   3. Push the branch and open a "Bump pygamine to vx.y.z" PR.
REM ---------------------------------------------------------------------------
