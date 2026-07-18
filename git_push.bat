@echo off
setlocal EnableDelayedExpansion

set "str01="
set "count=0"
for %%i in (%*) do (
    if !count! equ 0 (
        set "str01=%%i"
    ) else (
        set "str01=!str01! %%i"
    )
    set /a count+=1
)

git add *
git commit -m "!str01!"
git push
