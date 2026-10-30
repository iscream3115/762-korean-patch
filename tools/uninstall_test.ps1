# Removes the Korean patch test files from the game folder and restores vfs.ini.
$g = 'C:\Program Files (x86)\Steam\steamapps\common\7.62'
Get-Process EB -ErrorAction SilentlyContinue | Stop-Process -Force
foreach ($f in 'd3d9.dll', 'Korean.azp', 'kor_strings.txt', 'kor_quest.txt', 'kor_debug.txt', 'kor_d3d9.log', 'kor_nohla.txt') {
    Remove-Item (Join-Path $g $f) -ErrorAction SilentlyContinue
}
Remove-Item (Join-Path $g 'Korean') -Recurse -Force -ErrorAction SilentlyContinue
if (Test-Path "$g\INI\vfs.ini.kor_bak") {
    Copy-Item "$g\INI\vfs.ini.kor_bak" "$g\INI\vfs.ini" -Force
    Remove-Item "$g\INI\vfs.ini.kor_bak"
}
'Korean patch test files removed'
