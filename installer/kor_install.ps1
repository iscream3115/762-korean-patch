# 7.62 High Calibre (Blue Sun) Korean patch - installer.
# Run through install_korean.bat from the game folder (where EB.exe is).
# Adds "Korean.azp" to the top of INI\vfs.ini. The original is kept as INI\vfs.ini.kor_bak.
$ErrorActionPreference = 'Stop'
$g = $PSScriptRoot
if (-not (Test-Path (Join-Path $g 'EB.exe'))) {
    Write-Host '[ERROR] EB.exe not found. Extract the patch into the 7.62 game folder (the folder with EB.exe) and run again.'
    exit 1
}
foreach ($f in 'd3d9.dll', 'Korean.azp', 'kor_strings.txt', 'kor_quest.txt', 'Korean\Quests\E1P\e6q.txt') {
    if (-not (Test-Path (Join-Path $g $f))) { Write-Host "[ERROR] Missing file: $f"; exit 1 }
}
if (Get-Process EB -ErrorAction SilentlyContinue) { Write-Host '[ERROR] Close the game first.'; exit 1 }

$vfs = Join-Path $g 'INI\vfs.ini'
if (-not (Test-Path $vfs)) { Write-Host '[ERROR] INI\vfs.ini not found. Is Blue Sun installed?'; exit 1 }
if (-not (Test-Path "$vfs.kor_bak")) { Copy-Item $vfs "$vfs.kor_bak" }
$lines = @(Get-Content $vfs)
if ($lines | Where-Object { $_ -match '"Korean\.azp"' }) {
    Write-Host 'vfs.ini already has Korean.azp.'
} else {
    Set-Content $vfs -Encoding ascii -Value (@('"Korean.azp"         // Korean patch') + $lines)
    Write-Host 'vfs.ini updated.'
}
Write-Host 'Korean patch installed. Start the game as usual.'
