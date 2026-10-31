# 7.62 High Calibre (Blue Sun) Korean patch - uninstaller.
# Removes the patch files and restores INI\vfs.ini from INI\vfs.ini.kor_bak.
$g = $PSScriptRoot
if (Get-Process EB -ErrorAction SilentlyContinue) { Write-Host '[ERROR] Close the game first.'; exit 1 }
$vfs = Join-Path $g 'INI\vfs.ini'
if (Test-Path "$vfs.kor_bak") {
    Copy-Item "$vfs.kor_bak" $vfs -Force
    Remove-Item "$vfs.kor_bak"
} elseif (Test-Path $vfs) {
    $lines = @(Get-Content $vfs) | Where-Object { $_ -notmatch '"Korean\.azp"' }
    Set-Content $vfs -Encoding ascii -Value $lines
}
foreach ($f in 'd3d9.dll', 'Korean.azp', 'kor_strings.txt', 'kor_quest.txt', 'kor_debug.txt', 'kor_d3d9.log', 'kor_nohla.txt', 'launcher-x64.exe', 'launcher-ia32.exe') {
    Remove-Item (Join-Path $g $f) -ErrorAction SilentlyContinue
}
Remove-Item (Join-Path $g 'Korean') -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'Korean patch removed. (install_korean.bat, uninstall_korean.bat, kor_*.ps1 and the README can be deleted by hand.)'
