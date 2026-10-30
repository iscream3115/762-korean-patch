# usage: click.ps1 <x> <y> [proc=EB]   (client-area physical pixels, as in shot.ps1 output)
#        click.ps1 -key ESC
param([int]$x = -1, [int]$y = -1, [string]$proc = 'EB', [string]$key = '', [switch]$move)
Add-Type @'
using System; using System.Runtime.InteropServices;
public class C {
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, int f, int e);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@
[C]::SetProcessDPIAware() | Out-Null
$p = Get-Process $proc | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
$h = $p.MainWindowHandle
[C]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 200
if ($key) {
  $vk = @{ ESC = 0x1B; ENTER = 0x0D; SPACE = 0x20 }[$key]
  [C]::keybd_event($vk, 0, 0, 0); Start-Sleep -Milliseconds 60; [C]::keybd_event($vk, 0, 2, 0)
  "key $key"; return
}
$pt = New-Object C+POINT; $pt.X = $x; $pt.Y = $y
[C]::ClientToScreen($h, [ref]$pt) | Out-Null
[C]::SetCursorPos($pt.X, $pt.Y) | Out-Null
Start-Sleep -Milliseconds 150
if ($move) { "move $x $y"; return }
[C]::mouse_event(2, 0, 0, 0, 0); Start-Sleep -Milliseconds 60; [C]::mouse_event(4, 0, 0, 0, 0)
"clicked $x,$y"
