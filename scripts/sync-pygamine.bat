@echo off
REM Puts src/pygamine on the exact engine commit this project pins (the
REM submodule pointer in this repo). Run it after a pull or a branch switch,
REM or whenever the engine folder looks out of step. Safe to run any time: it
REM never moves the pin and never changes what this repo has committed.
cd /d "%~dp0.."
git submodule update --init src/pygamine
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
