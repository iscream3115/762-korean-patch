// Steam launcher stand-in for 7.62 High Calibre (Blue Sun branch).
// Steam's launch config now points at launcher-x64.exe / launcher-ia32.exe, which the
// community_patch_and_bsm branch does not ship. This starts EB.exe from the same folder
// with the same arguments. HLA.dll is loaded by the Korean patch's d3d9.dll, so the
// Blue Sun launcher E6.exe (often quarantined by antivirus) is not needed.
#include <windows.h>
#include <stdio.h>

int WINAPI wWinMain(HINSTANCE hi, HINSTANCE hp, LPWSTR args, int show) {
    wchar_t dir[MAX_PATH], exe[MAX_PATH], dll[MAX_PATH], cmd[32768];
    GetModuleFileNameW(NULL, dir, MAX_PATH);
    wchar_t* slash = wcsrchr(dir, L'\\');
    if (slash) *slash = 0;
    swprintf(exe, MAX_PATH, L"%s\\EB.exe", dir);
    swprintf(dll, MAX_PATH, L"%s\\d3d9.dll", dir);

    if (GetFileAttributesW(exe) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL, L"EB.exe를 찾을 수 없습니다. 게임 폴더에 이 파일을 두세요.", L"7.62 launcher", MB_ICONERROR);
        return 1;
    }
    if (GetFileAttributesW(dll) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL,
            L"d3d9.dll(한글 패치)이 없습니다.\n"
            L"Blue Sun은 HLA.dll이 필요한데, 이 런처는 한글 패치의 d3d9.dll이 HLA.dll을 불러오는 것을 전제로 합니다.\n"
            L"한글 패치를 설치한 뒤 다시 실행하세요.",
            L"7.62 launcher", MB_ICONWARNING);
        return 1;
    }

    swprintf(cmd, 32768, L"\"%s\" %s", exe, args ? args : L"");
    STARTUPINFOW si = {sizeof si};
    PROCESS_INFORMATION pi;
    if (!CreateProcessW(exe, cmd, NULL, NULL, FALSE, 0, NULL, dir, &si, &pi)) {
        wchar_t msg[256];
        swprintf(msg, 256, L"EB.exe 실행 실패 (오류 %lu)", GetLastError());
        MessageBoxW(NULL, msg, L"7.62 launcher", MB_ICONERROR);
        return 1;
    }
    // Wait so Steam shows the game as running until EB.exe exits.
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD code = 0;
    GetExitCodeProcess(pi.hProcess, &code);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return (int)code;
}
