# Starts EB.exe, clicks through to a new game and screenshots the intro dialog.
# usage: test_newgame.ps1 <out.png> [-Advance]   (-Advance clicks once more to pass the intro)
param([string]$out, [switch]$Advance)
$g = 'C:\Program Files (x86)\Steam\steamapps\common\7.62'
$t = $PSScriptRoot
Get-Process EB -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process EB -ErrorAction SilentlyContinue | Wait-Process -Timeout 15
Remove-Item "$g\kor_d3d9.log" -ErrorAction SilentlyContinue
Start-Process -FilePath "$g\EB.exe" -WorkingDirectory $g
Start-Sleep 25
& "$t\click.ps1" 651 402; Start-Sleep 6      # NEW GAME
& "$t\click.ps1" 853 857; Start-Sleep 8      # difficulty warning: YES
& "$t\click.ps1" 1838 1221; Start-Sleep 4    # START GAME
& "$t\click.ps1" 853 857; Start-Sleep 40     # unspent points: YES
if ($Advance) { & "$t\click.ps1" 1000 700; Start-Sleep 5 }
powershell -NoProfile -File "$t\shot.ps1" $out
