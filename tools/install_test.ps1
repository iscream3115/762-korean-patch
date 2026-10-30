# Installs the current build into the game folder for testing.
# Undo with tools\uninstall_test.ps1. Original game files are never overwritten:
# translated loose files go to <game>\Korean\ and the DLL redirects reads there.
$g = 'C:\Program Files (x86)\Steam\steamapps\common\7.62'
$b = Join-Path $PSScriptRoot '..\build'
Get-Process EB -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process EB -ErrorAction SilentlyContinue | Wait-Process -Timeout 15
Start-Sleep -Milliseconds 500

Copy-Item "$b\d3d9.dll", "$b\Korean.azp" $g -Force
if (Test-Path "$b\kor_strings.txt") { Copy-Item "$b\kor_strings.txt" $g -Force }
if (Test-Path "$b\kor_quest.txt") { Copy-Item "$b\kor_quest.txt" $g -Force }

$k = Join-Path $g 'Korean'
if (Test-Path "$b\e6q.txt") {
    New-Item -ItemType Directory -Force "$k\Quests\E1P" | Out-Null
    Copy-Item "$b\e6q.txt" "$k\Quests\E1P\e6q.txt" -Force
}

$vfs = "$g\INI\vfs.ini"
if (-not (Test-Path "$vfs.kor_bak")) { Copy-Item $vfs "$vfs.kor_bak" }
$lines = Get-Content $vfs
if (-not ($lines | Where-Object { $_ -match '"Korean\.azp"' })) {
    Set-Content $vfs -Encoding ascii -Value (@('"Korean.azp"         // Korean patch') + $lines)
}
'Korean patch test files installed'
