# New game, then intro -> continue -> first class option, and screenshot after each step.
param([string]$prefix)
$t = $PSScriptRoot
& "$t\test_newgame.ps1" "$prefix-0.png"
& "$t\click.ps1" 1000 700; Start-Sleep 4        # [click to continue]
powershell -NoProfile -File "$t\shot.ps1" "$prefix-1.png"
& "$t\click.ps1" 493 612; Start-Sleep 4         # answer 1: (Continue with character creation)
powershell -NoProfile -File "$t\shot.ps1" "$prefix-2.png"
& "$t\click.ps1" 493 612; Start-Sleep 6         # answer 1: first class
powershell -NoProfile -File "$t\shot.ps1" "$prefix-3.png"
