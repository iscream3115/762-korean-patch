# Automated character-creation check driven by the DLL draw log (needs kor_debug.txt).
# New game -> intro -> continue -> first class -> finish -> close screen; then checks the HUD.
# Prints PASS/FAIL and saves <prefix>-*.png screenshots.
param([string]$prefix)
$g = 'C:\Program Files (x86)\Steam\steamapps\common\7.62'
$t = $PSScriptRoot
$log = "$g\kor_d3d9.log"
$enc = [Text.Encoding]::GetEncoding(949)

function LogText { if (Test-Path $log) { [IO.File]::ReadAllText($log, $enc) } else { '' } }
function WaitFor([string]$pattern, [int]$sec) {
    $end = (Get-Date).AddSeconds($sec)
    while ((Get-Date) -lt $end) { if ((LogText) -match $pattern) { return $true }; Start-Sleep -Milliseconds 500 }
    return $false
}
function Shot([string]$n) { powershell -NoProfile -File "$t\shot.ps1" "$prefix-$n.png" | Out-Null }

New-Item -ItemType File -Force "$g\kor_debug.txt" | Out-Null
Get-Process EB -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process EB -ErrorAction SilentlyContinue | Wait-Process -Timeout 15
Start-Sleep 1
Remove-Item $log -ErrorAction SilentlyContinue
Start-Process -FilePath "$g\EB.exe" -WorkingDirectory $g

if (-not (WaitFor 'draw f\d+: 1\.11 Build' 60)) { 'FAIL main menu'; exit }
Start-Sleep 3
& "$t\click.ps1" 651 402 | Out-Null; Start-Sleep 5      # NEW GAME
& "$t\click.ps1" 853 857 | Out-Null; Start-Sleep 6      # difficulty warning: YES
& "$t\click.ps1" 1838 1221 | Out-Null; Start-Sleep 4    # START GAME
& "$t\click.ps1" 853 857 | Out-Null                     # unspent points: YES
if (-not (WaitFor 'Blue Sun System|\uBE14\uB8E8 \uC120 \uC2DC\uC2A4\uD15C' 120)) { Shot 'nointro'; 'FAIL no intro'; exit }
Start-Sleep 3
Shot 1
& "$t\click.ps1" 1000 700 | Out-Null; Start-Sleep 3     # [click to continue]
Shot 2
& "$t\click.ps1" 493 612 | Out-Null; Start-Sleep 3      # answer 1: continue with character creation
Shot 3
& "$t\click.ps1" 493 612 | Out-Null; Start-Sleep 6      # answer 1: first class
Shot 4
if (-not ((LogText) -match 'Attribute Points Left|\uB0A8\uC740 \uB2A5\uB825\uCE58')) { 'FAIL no attribute dialog'; exit }
& "$t\click.ps1" 493 673 | Out-Null; Start-Sleep 5      # answer 3: complete character creation
Shot 5
& "$t\click.ps1" 493 673 | Out-Null; Start-Sleep 8      # answer 3: close screen
Shot 6
Add-Type -AssemblyName System.Drawing
$b = [Drawing.Bitmap]::FromFile("$prefix-6.png"); $sum = 0; $n = 0
for ($x = 1960; $x -lt 2080; $x += 4) { for ($y = 1050; $y -lt 1290; $y += 4) { $c = $b.GetPixel($x, $y); $sum += $c.R + $c.G + $c.B; $n++ } }
$b.Dispose(); $avg = [int]($sum / $n / 3)
if ($avg -gt 25) { "PASS hud=$avg" } else { "FAIL no hud ($avg)" }
