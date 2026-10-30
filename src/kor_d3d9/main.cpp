// 7.62 High Calibre Korean text renderer (d3d9.dll proxy).
//
// EB.exe 1.11 b286 draws 2D text with SManager2D::DrawString (0x685CD0) using
// 224-glyph single-byte bitmap fonts. This DLL replaces that function and the
// string-width function (0x684060) so CP949 double-byte characters are drawn
// from a glyph cache rendered with GDI, while single-byte runs still go
// through the game's original code.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <intrin.h>
#include <d3d9.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <unordered_map>
#include <string>

// ---------------------------------------------------------------- proxy ---
static HMODULE g_real;
static FARPROC real(const char* name) {
    if (!g_real) {
        char p[MAX_PATH];
        GetSystemDirectoryA(p, MAX_PATH);
        strcat_s(p, "\\d3d9.dll");
        g_real = LoadLibraryA(p);
    }
    return g_real ? GetProcAddress(g_real, name) : nullptr;
}

extern "C" {
IDirect3D9* WINAPI P_Direct3DCreate9(UINT v) {
    typedef IDirect3D9*(WINAPI * F)(UINT);
    static F f = (F)real("Direct3DCreate9");
    return f ? f(v) : nullptr;
}
HRESULT WINAPI P_Direct3DCreate9Ex(UINT v, void** out) {
    typedef HRESULT(WINAPI * F)(UINT, void**);
    static F f = (F)real("Direct3DCreate9Ex");
    return f ? f(v, out) : E_FAIL;
}
int WINAPI P_D3DPERF_BeginEvent(DWORD c, LPCWSTR n) {
    typedef int(WINAPI * F)(DWORD, LPCWSTR);
    static F f = (F)real("D3DPERF_BeginEvent");
    return f ? f(c, n) : 0;
}
int WINAPI P_D3DPERF_EndEvent() {
    typedef int(WINAPI * F)();
    static F f = (F)real("D3DPERF_EndEvent");
    return f ? f() : 0;
}
void WINAPI P_D3DPERF_SetMarker(DWORD c, LPCWSTR n) {
    typedef void(WINAPI * F)(DWORD, LPCWSTR);
    static F f = (F)real("D3DPERF_SetMarker");
    if (f) f(c, n);
}
void WINAPI P_D3DPERF_SetRegion(DWORD c, LPCWSTR n) {
    typedef void(WINAPI * F)(DWORD, LPCWSTR);
    static F f = (F)real("D3DPERF_SetRegion");
    if (f) f(c, n);
}
BOOL WINAPI P_D3DPERF_QueryRepeatFrame() {
    typedef BOOL(WINAPI * F)();
    static F f = (F)real("D3DPERF_QueryRepeatFrame");
    return f ? f() : FALSE;
}
void WINAPI P_D3DPERF_SetOptions(DWORD o) {
    typedef void(WINAPI * F)(DWORD);
    static F f = (F)real("D3DPERF_SetOptions");
    if (f) f(o);
}
DWORD WINAPI P_D3DPERF_GetStatus() {
    typedef DWORD(WINAPI * F)();
    static F f = (F)real("D3DPERF_GetStatus");
    return f ? f() : 0;
}
}

// ------------------------------------------------------------------ log ---
static char g_dir[MAX_PATH];
static void logf(const char* fmt, ...) {
    char path[MAX_PATH];
    sprintf_s(path, "%s\\kor_d3d9.log", g_dir);
    FILE* f = nullptr;
    if (fopen_s(&f, path, "a") || !f) return;
    va_list ap;
    va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);
    fputc('\n', f);
    fclose(f);
}

// ------------------------------------------------------------- game data ---
// SFont layout (SFont::LoadFont 0x68A500)
struct Glyph { float u0, v0, u1, v1; };            // index c-0x20, at +0x5C
static inline unsigned font_flags(char* f) { return *(unsigned*)(f + 0x54); }
static inline float font_scale(char* f) { return *(float*)(f + 0x58); }
static inline Glyph* font_glyphs(char* f) { return (Glyph*)(f + 0x5C); }
static inline unsigned font_texw(char* f) { return *(unsigned*)(f + 0xE60); }
static inline unsigned font_texh(char* f) { return *(unsigned*)(f + 0xE64); }

// SManager2D queued string (item + 0x6C, stride 0xB0)
struct TextItem {
    const char* str;
    int x, y;
    DWORD color;
    int font;
};

struct Vtx { float x, y, z, rhw; DWORD c; float u, v; };   // FVF 0x144

static const DWORD A_DRAWSTRING = 0x685CD0;
static const DWORD A_WIDTH = 0x684060;
static const DWORD A_MGRPTR = 0x7FCE94;

typedef void(__fastcall* DrawStringFn)(void* mgr, void* edx, TextItem* it);
static DrawStringFn o_DrawString;

// ------------------------------------------------------------ korean ---
// KS X 1001 (EUC-KR) range only. CP949's extended range would misread
// English cp1252 text such as "character\x92s" (0x92 0x73) as Hangul.
static inline bool is_lead(unsigned char c) { return c >= 0xA1 && c <= 0xFE; }
static inline bool is_trail(unsigned char c) { return c >= 0xA1 && c <= 0xFE; }
// Only treat as Korean when the pair decodes to a CJK/Hangul code point, so
// existing cp1252 accented text (e.g. "é ") keeps working.
static wchar_t decode_pair(const unsigned char* s) {
    if (!is_lead(s[0]) || !is_trail(s[1])) return 0;
    wchar_t w = 0;
    if (MultiByteToWideChar(949, MB_ERR_INVALID_CHARS, (const char*)s, 2, &w, 1) != 1) return 0;
    return w;
}

// ---------------------------------------------------------- glyph cache ---
static const int TEX = 1024;
static IDirect3DDevice9* g_dev;
static IDirect3DTexture9* g_tex;
static int g_penX, g_penY, g_rowH;

struct Slot { short x, y, w, h; };
static std::unordered_map<unsigned long long, Slot> g_cache;
static std::unordered_map<int, HFONT> g_fonts;
static HDC g_dc;
static wchar_t g_face[64] = L"Malgun Gothic";

static void cache_reset() {
    g_cache.clear();
    g_penX = g_penY = g_rowH = 0;
    if (g_tex) {
        D3DLOCKED_RECT lr;
        if (SUCCEEDED(g_tex->LockRect(0, &lr, nullptr, 0))) {
            for (int y = 0; y < TEX; y++) memset((char*)lr.pBits + y * lr.Pitch, 0, TEX * 4);
            g_tex->UnlockRect(0);
        }
    }
}

static bool ensure_tex(IDirect3DDevice9* dev) {
    if (dev != g_dev) {
        if (g_tex) { g_tex->Release(); g_tex = nullptr; }
        g_dev = dev;
        g_cache.clear();
    }
    if (!g_tex) {
        HRESULT hr = dev->CreateTexture(TEX, TEX, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &g_tex, nullptr);
        if (FAILED(hr)) { logf("CreateTexture failed %08lx", hr); g_tex = nullptr; return false; }
        cache_reset();
    }
    return true;
}

static HFONT get_hfont(int px) {
    auto it = g_fonts.find(px);
    if (it != g_fonts.end()) return it->second;
    HFONT f = CreateFontW(-px, 0, 0, 0, FW_NORMAL, 0, 0, 0, HANGUL_CHARSET, OUT_TT_PRECIS,
                          CLIP_DEFAULT_PRECIS, ANTIALIASED_QUALITY, DEFAULT_PITCH, g_face);
    g_fonts[px] = f;
    return f;
}

// cell height in screen pixels for one game font (space glyph = line box)
static int cell_h(char* f) {
    Glyph& g = font_glyphs(f)[0];
    int h = (int)lroundf(font_texh(f) * (g.v1 - g.v0));
    return h < 6 ? 6 : h;
}

static HFONT get_hfont(int px);
static int em_px(int cellH) { return (int)lroundf(cellH * 0.85f); }

// advance = measured width of a full Hangul syllable at this size
static int advance_px(int cellH) {
    static std::unordered_map<int, int> adv;
    auto it = adv.find(cellH);
    if (it != adv.end()) return it->second;
    if (!g_dc) g_dc = CreateCompatibleDC(nullptr);
    HGDIOBJ of = SelectObject(g_dc, get_hfont(em_px(cellH)));
    SIZE sz = {};
    GetTextExtentPoint32W(g_dc, L"\xAC00", 1, &sz);
    SelectObject(g_dc, of);
    int a = sz.cx > 0 ? sz.cx : em_px(cellH);
    adv[cellH] = a;
    return a;
}

static bool get_glyph(int cellH, bool framed, wchar_t wc, Slot& out) {
    unsigned long long key = ((unsigned long long)cellH << 40) | ((unsigned long long)framed << 32) | wc;
    auto it = g_cache.find(key);
    if (it != g_cache.end()) { out = it->second; return true; }

    int w = advance_px(cellH) + (framed ? 1 : 0), h = cellH;
    if (g_penX + w + 1 > TEX) { g_penX = 0; g_penY += g_rowH + 1; g_rowH = 0; }
    if (g_penY + h + 1 > TEX) { logf("glyph cache full, reset"); cache_reset(); }

    // render white-on-black with GDI
    if (!g_dc) g_dc = CreateCompatibleDC(nullptr);
    BITMAPINFO bi = {};
    bi.bmiHeader.biSize = sizeof(bi.bmiHeader);
    bi.bmiHeader.biWidth = w;
    bi.bmiHeader.biHeight = -h;
    bi.bmiHeader.biPlanes = 1;
    bi.bmiHeader.biBitCount = 32;
    void* bits = nullptr;
    HBITMAP bmp = CreateDIBSection(g_dc, &bi, DIB_RGB_COLORS, &bits, nullptr, 0);
    if (!bmp) return false;
    HGDIOBJ ob = SelectObject(g_dc, bmp);
    HGDIOBJ of = SelectObject(g_dc, get_hfont(em_px(cellH)));
    memset(bits, 0, w * h * 4);
    SetBkMode(g_dc, TRANSPARENT);
    SetTextColor(g_dc, RGB(255, 255, 255));
    RECT rc = {0, 0, w - (framed ? 1 : 0), h};
    DrawTextW(g_dc, &wc, 1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX);
    GdiFlush();

    D3DLOCKED_RECT lr;
    RECT dst = {g_penX, g_penY, g_penX + w, g_penY + h};
    if (SUCCEEDED(g_tex->LockRect(0, &lr, &dst, 0))) {
        const DWORD* src = (const DWORD*)bits;
        for (int y = 0; y < h; y++) {
            DWORD* row = (DWORD*)((char*)lr.pBits + y * lr.Pitch);
            for (int x = 0; x < w; x++) {
                int core = src[y * w + x] & 0xFF;
                int a = core;
                if (framed) {
                    int o = 0;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++) {
                            int xx = x + dx, yy = y + dy;
                            if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue;
                            int v = src[yy * w + xx] & 0xFF;
                            if (v > o) o = v;
                        }
                    a = o > core ? o : core;
                }
                int c = a ? core * 255 / a : 0;
                row[x] = ((DWORD)a << 24) | (c << 16) | (c << 8) | c;
            }
        }
        g_tex->UnlockRect(0);
    }
    SelectObject(g_dc, of);
    SelectObject(g_dc, ob);
    DeleteObject(bmp);

    out = {(short)g_penX, (short)g_penY, (short)w, (short)h};
    g_cache[key] = out;
    g_penX += w + 1;
    if (h > g_rowH) g_rowH = h;
    return true;
}

// ------------------------------------------------- display substitution ---
// kor_strings.txt (UTF-8): "original<TAB>translation" per line, '#' comments.
// Whole-string match at draw/measure time; used for text that cannot be
// changed in data files (strings built in code, item names used as keys).
static std::unordered_map<std::string, std::string> g_subst;

static std::string conv(const std::string& s, UINT from, UINT to) {
    int n = MultiByteToWideChar(from, 0, s.c_str(), (int)s.size(), nullptr, 0);
    std::wstring w(n, 0);
    MultiByteToWideChar(from, 0, s.c_str(), (int)s.size(), &w[0], n);
    int m = WideCharToMultiByte(to, 0, w.c_str(), n, nullptr, 0, nullptr, nullptr);
    std::string o(m, 0);
    WideCharToMultiByte(to, 0, w.c_str(), n, &o[0], m, nullptr, nullptr);
    return o;
}

static void load_subst() {
    char path[MAX_PATH];
    sprintf_s(path, "%s\\kor_strings.txt", g_dir);
    FILE* f = nullptr;
    if (fopen_s(&f, path, "rb") || !f) return;
    char line[4096];
    while (fgets(line, sizeof line, f)) {
        char* s = line;
        if ((unsigned char)s[0] == 0xEF && (unsigned char)s[1] == 0xBB && (unsigned char)s[2] == 0xBF) s += 3;
        size_t n = strlen(s);
        while (n && (s[n - 1] == '\n' || s[n - 1] == '\r')) s[--n] = 0;
        if (!n || s[0] == '#') continue;
        char* tab = strchr(s, '\t');
        if (!tab) continue;
        *tab = 0;
        g_subst[conv(s, CP_UTF8, 1252)] = conv(tab + 1, CP_UTF8, 949);
    }
    fclose(f);
    logf("substitutions: %u", (unsigned)g_subst.size());
}

static const char* subst(const char* s) {
    if (g_subst.empty() || !s || !*s) return s;
    auto it = g_subst.find(s);
    return it == g_subst.end() ? s : it->second.c_str();
}

// ------------------------------------------------------------- hooks ---
static bool has_korean(const char* s) {
    for (const unsigned char* p = (const unsigned char*)s; *p; p++)
        if (*p >= 0x81 && p[1] && decode_pair(p)) return true;
    return false;
}

static int __cdecl h_Width(const char* s, int font) {
    if (!s) return 0;
    s = subst(s);
    char* mgr = *(char**)A_MGRPTR;
    char* f = ((char**)mgr)[font];
    Glyph* g = font_glyphs(f);
    float du = 0.0f;
    int kor = 0, ch = 0;
    for (const unsigned char* p = (const unsigned char*)s; *p; p++) {
        if (*p >= 0x81 && p[1] && decode_pair(p)) {
            if (!ch) ch = cell_h(f);
            kor += advance_px(ch);
            p++;
            continue;
        }
        if (*p >= 0x20) du += g[*p - 0x20].u1 - g[*p - 0x20].u0;
    }
    return (int)(du * (float)font_texw(f)) + kor;
}

static bool g_debug;
static void debug_seen(const char* s, int font) {
    static std::unordered_map<std::string, int> seen;
    if (seen.size() > 4000) return;
    std::string k(s);
    if (seen.emplace(k, font).second) logf("draw f%d: %s", font, s);
}

static void __fastcall h_DrawString(char* mgr, void* edx, TextItem* it) {
    if (g_debug && it->str) debug_seen(it->str, it->font);
    TextItem sub;
    if (it->str) {
        const char* r = subst(it->str);
        if (r != it->str) { sub = *it; sub.str = r; it = &sub; }
    }
    if (!it->str || !has_korean(it->str)) { o_DrawString(mgr, edx, it); return; }

    char* f = ((char**)mgr)[it->font];
    Glyph* g = font_glyphs(f);
    float scale = font_scale(f);
    float texw = (float)font_texw(f), texh = (float)font_texh(f);
    float lineH = texh * (g[0].v1 - g[0].v0);
    int ch = cell_h(f);
    bool framed = (font_flags(f) & 4) != 0;

    IDirect3DVertexBuffer9* vb = *(IDirect3DVertexBuffer9**)(mgr + 0x64);
    IDirect3DDevice9* dev = nullptr;
    if (!vb || FAILED(vb->GetDevice(&dev)) || !dev) { o_DrawString(mgr, edx, it); return; }
    dev->Release();
    if (!ensure_tex(dev)) { o_DrawString(mgr, edx, it); return; }

    static Vtx verts[6 * 512];
    int nv = 0;
    char run[1024];
    float x = (float)it->x, y = (float)it->y, x0 = x;
    const unsigned char* p = (const unsigned char*)it->str;

    while (*p) {
        // single-byte run
        int n = 0;
        float runw = 0.0f;
        while (*p && *p != '\n' && !(*p >= 0x81 && p[1] && decode_pair(p)) && n < (int)sizeof(run) - 1) {
            if (*p >= 0x20) runw += texw * (g[*p - 0x20].u1 - g[*p - 0x20].u0) / scale;
            run[n++] = (char)*p++;
        }
        if (n) {
            run[n] = 0;
            TextItem t = *it;
            t.str = run;
            t.x = (int)lroundf(x);
            t.y = (int)lroundf(y);
            o_DrawString(mgr, edx, &t);
            x += runw;
        }
        if (!*p) break;
        if (*p == '\n') { x = x0; y += lineH; p++; continue; }
        wchar_t wc = decode_pair(p);
        if (!wc) { p++; continue; }
        p += 2;
        Slot s;
        if (!get_glyph(ch, framed, wc, s)) { x += advance_px(ch); continue; }
        if (nv + 6 > (int)(sizeof(verts) / sizeof(verts[0]))) break;
        float l = floorf(x) - 0.5f, t = floorf(y) - 0.5f, r = l + s.w, b = t + s.h;
        float u0 = s.x / (float)TEX, v0 = s.y / (float)TEX;
        float u1 = (s.x + s.w) / (float)TEX, v1 = (s.y + s.h) / (float)TEX;
        Vtx q[4] = {{l, t, 1, 1, it->color, u0, v0}, {r, t, 1, 1, it->color, u1, v0},
                    {r, b, 1, 1, it->color, u1, v1}, {l, b, 1, 1, it->color, u0, v1}};
        verts[nv++] = q[0]; verts[nv++] = q[1]; verts[nv++] = q[2];
        verts[nv++] = q[0]; verts[nv++] = q[2]; verts[nv++] = q[3];
        x += advance_px(ch);
    }

    if (nv) {
        IDirect3DBaseTexture9* prev = nullptr;
        dev->GetTexture(0, &prev);
        dev->SetTexture(0, g_tex);
        dev->SetFVF(D3DFVF_XYZRHW | D3DFVF_DIFFUSE | D3DFVF_TEX1);
        dev->DrawPrimitiveUP(D3DPT_TRIANGLELIST, nv / 3, verts, sizeof(Vtx));
        dev->SetStreamSource(0, vb, 0, sizeof(Vtx));
        dev->SetTexture(0, prev);
        if (prev) prev->Release();
    }
}



// ------------------------------------------------- text-to-bitmap path ---
// DrawTextToBitmapMF 0x683C10 cdecl(x, y, str, color, Bitmap* target, font):
// copies each glyph from the font texture (A4 coverage, low nibble = shade)
// into the target bitmap's A8R8G8B8 texture as (A*a, R*v, G*v, B*v).
// Used for tooltips and the name labels over NPCs. Korean pairs are
// rendered with GDI here; single-byte runs still go through the original.
static const DWORD A_TEXTBMP = 0x683C10;
static const DWORD A_BMP_TEX = 0x6893D0;   // thiscall(Bitmap*) -> IDirect3DTexture9*
static const DWORD A_BMP_DIRTY = 0x712C2C;
typedef void(__cdecl* TextBmpFn)(int x, int y, const char* s, DWORD color, char* tgt, int font);
typedef IDirect3DTexture9*(__fastcall* BmpTexFn)(char* bmp, void* edx);
static TextBmpFn o_TextBmp;

static void bmp_glyph(char* tgt, int x, int y, int cellH, bool framed, wchar_t wc, DWORD color) {
    int w = advance_px(cellH) + (framed ? 1 : 0), h = cellH;
    int bw = *(int*)(tgt + 0x28), bh = *(int*)(tgt + 0x2C);
    if (x >= bw || y >= bh || x + w <= 0 || y + h <= 0) return;
    if (!g_dc) g_dc = CreateCompatibleDC(nullptr);
    BITMAPINFO bi = {};
    bi.bmiHeader.biSize = sizeof(bi.bmiHeader);
    bi.bmiHeader.biWidth = w;
    bi.bmiHeader.biHeight = -h;
    bi.bmiHeader.biPlanes = 1;
    bi.bmiHeader.biBitCount = 32;
    void* bits = nullptr;
    HBITMAP bmp = CreateDIBSection(g_dc, &bi, DIB_RGB_COLORS, &bits, nullptr, 0);
    if (!bmp) return;
    HGDIOBJ ob = SelectObject(g_dc, bmp);
    HGDIOBJ of = SelectObject(g_dc, get_hfont(em_px(cellH)));
    memset(bits, 0, w * h * 4);
    SetBkMode(g_dc, TRANSPARENT);
    SetTextColor(g_dc, RGB(255, 255, 255));
    RECT rc = {0, 0, w - (framed ? 1 : 0), h};
    DrawTextW(g_dc, &wc, 1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX);
    GdiFlush();

    int x0 = x < 0 ? 0 : x, y0 = y < 0 ? 0 : y;
    int x1 = x + w > bw ? bw : x + w, y1 = y + h > bh ? bh : y + h;
    IDirect3DTexture9* tex = ((BmpTexFn)A_BMP_TEX)(tgt, nullptr);
    D3DLOCKED_RECT lr;
    RECT dst = {x0, y0, x1, y1};
    if (tex && SUCCEEDED(tex->LockRect(0, &lr, &dst, 0))) {
        const DWORD* src = (const DWORD*)bits;
        unsigned A = color >> 24, R = (color >> 16) & 0xFF, G = (color >> 8) & 0xFF, B = color & 0xFF;
        for (int yy = y0; yy < y1; yy++) {
            DWORD* row = (DWORD*)((char*)lr.pBits + (yy - y0) * lr.Pitch);
            for (int xx = x0; xx < x1; xx++) {
                int gx = xx - x, gy = yy - y;
                int core = src[gy * w + gx] & 0xFF, a = core;
                if (framed) {
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++) {
                            int sx = gx + dx, sy = gy + dy;
                            if (sx < 0 || sy < 0 || sx >= w || sy >= h) continue;
                            int v = src[sy * w + sx] & 0xFF;
                            if (v > a) a = v;
                        }
                }
                if (!a) continue;
                int v = framed ? core * 255 / a : 255;
                row[xx - x0] = ((A * a / 255) << 24) | ((R * v / 255) << 16) | ((G * v / 255) << 8) | (B * v / 255);
            }
        }
        tex->UnlockRect(0);
    }
    SelectObject(g_dc, of);
    SelectObject(g_dc, ob);
    DeleteObject(bmp);
}

static void __cdecl h_TextBmp(int x, int y, const char* s, DWORD color, char* tgt, int font) {
    if (s) s = subst(s);
    if (g_debug && s) debug_seen(s, 100 + font);
    if (g_debug && s && s[0] && !s[1]) {
        static std::unordered_map<DWORD, int> seen;
        DWORD ra = (DWORD)_ReturnAddress();
        if (seen.size() < 50 && seen.emplace(ra, 1).second) logf("bmp char caller %08X %02X f%d x%d y%d", ra, (unsigned char)s[0], font, x, y);
    }
    if (!s || !tgt || !has_korean(s) || *(int*)(tgt + 4) == 3) { o_TextBmp(x, y, s, color, tgt, font); return; }
    char* f = (*(char***)A_MGRPTR)[font];
    Glyph* g = font_glyphs(f);
    float W = (float)font_texw(f);
    int ch = cell_h(f);
    bool framed = (font_flags(f) & 4) != 0;
    char run[1024];
    const unsigned char* p = (const unsigned char*)s;
    while (*p) {
        int n = 0, runw = 0;
        while (*p && !(*p >= 0x81 && p[1] && decode_pair(p)) && n < (int)sizeof(run) - 1) {
            if (*p >= 0x20) runw += (int)(g[*p - 0x20].u1 * W) - (int)(g[*p - 0x20].u0 * W);
            run[n++] = (char)*p++;
        }
        if (n) { run[n] = 0; o_TextBmp(x, y, run, color, tgt, font); x += runw; }
        if (!*p) break;
        wchar_t wc = decode_pair(p);
        p += 2;
        bmp_glyph(tgt, x, y, ch, framed, wc, color);
        x += advance_px(ch);
    }
    tgt[0x1D] = *(char*)A_BMP_DIRTY;
}


// Tooltip text 0x428910 thiscall(self, Bitmap* bmp, str, x, y, font):
// draws one byte at a time through DrawTextToBitmapMF, so Korean pairs get
// split. For Korean text, draw each line whole through h_TextBmp instead.
static const DWORD A_TIPTEXT = 0x428910;
typedef void(__fastcall* TipTextFn)(char* self, void* edx, char* bmp, const char* s, int x, int y, int font);
static TipTextFn o_TipText;
static void __fastcall h_TipText(char* self, void* edx, char* bmp, const char* s, int x, int y, int font) {
    if (!s || !bmp || !has_korean(subst(s))) { o_TipText(self, edx, bmp, s, x, y, font); return; }
    s = subst(s);
    int h = ((int(__cdecl*)(const char*, int))0x6840D0)((const char*)0x6EE7FC, font);
    int lineH = (int)((float)h * *(float*)0x6EE7F8);
    DWORD color = *(DWORD*)(self + 0x6BC);
    float limit = *(float*)(bmp + 0x40) - (float)lineH;
    char line[1024];
    while (*s) {
        int n = 0;
        while (*s && *s != '\n' && n < (int)sizeof(line) - 1) line[n++] = *s++;
        line[n] = 0;
        if (n && (float)y < limit) h_TextBmp(x, y, line, color, bmp, font);
        if (*s == '\n') { s++; y += lineH; }
        else if (*s) s++;
    }
}

// ------------------------------------------------------ AddString wrapper ---
// 0x6866A0 cdecl(x, y, str, color, font) -> SManager2D::AddString(mgr, x, y, font, color, str)
static const DWORD A_ADDTEXT = 0x6866A0;
static const DWORD A_ADDSTRING = 0x6844E0;
typedef void(__fastcall* AddStringFn)(void* mgr, void* edx, int x, int y, int font, DWORD color, const char* s);
static void __cdecl h_AddText(int x, int y, const char* s, DWORD color, int font) {
    if (g_debug && s && s[0] && !s[1]) {
        static std::unordered_map<DWORD, int> seen;
        DWORD ra = (DWORD)_ReturnAddress();
        if (seen.size() < 200 && seen.emplace(ra, 1).second) logf("char caller %08X '%c' f%d x%d y%d", ra, s[0], font, x, y);
    }
    ((AddStringFn)A_ADDSTRING)(*(void**)A_MGRPTR, nullptr, x, y, font, color, s);
}

// ------------------------------------------------------------ install ---
static bool patch_jmp(DWORD at, void* to) {
    DWORD old;
    if (!VirtualProtect((void*)at, 5, PAGE_EXECUTE_READWRITE, &old)) return false;
    *(BYTE*)at = 0xE9;
    *(DWORD*)(at + 1) = (DWORD)to - at - 5;
    VirtualProtect((void*)at, 5, old, &old);
    FlushInstructionCache(GetCurrentProcess(), (void*)at, 5);
    return true;
}

// ------------------------------------------------------ quest literals ---
// Blue Sun's quest scripts (.qst/.gen bytecode) carry their dialogue as
// encrypted string literals instead of IDs into e6q.txt. Both script loaders
// (from file 0x698EF0, from memory 0x6994B0) build a node tree and recurse
// through their own entry point; string-literal nodes have type 0x23 with the
// decrypted text at node[2] and its size incl. NUL at node[3]. We let the
// original build each node, then swap matching text from kor_quest.txt
// (UTF-8 "english<TAB>korean"). Strings are allocated the way the game
// allocates them (pool below 0xDD bytes, operator new above) so frees match.
static const DWORD A_NODE_FILE = 0x698EF0;
static const DWORD A_NODE_MEM = 0x6994B0;
static const DWORD A_POOL_ALLOC = 0x6AB6D0;  // thiscall(pool, size), pool = *0xA11BFC
static const DWORD A_OPNEW = 0x6BD299;
typedef int* (__cdecl* NodeFn)(void*, int, int);
typedef void* (__fastcall* PoolAllocFn)(void* pool, int edx, int size);
typedef void* (__cdecl* OpNewFn)(unsigned);
static NodeFn o_node_file, o_node_mem;
static std::unordered_map<std::string, std::string> g_quest;
static unsigned g_quest_hits;

static void load_quest() {
    char path[MAX_PATH];
    sprintf_s(path, "%s\\kor_quest.txt", g_dir);
    FILE* f = nullptr;
    if (fopen_s(&f, path, "rb") || !f) return;
    static char line[65536];
    while (fgets(line, sizeof line, f)) {
        char* s = line;
        if ((unsigned char)s[0] == 0xEF && (unsigned char)s[1] == 0xBB && (unsigned char)s[2] == 0xBF) s += 3;
        size_t n = strlen(s);
        while (n && (s[n - 1] == '\n' || s[n - 1] == '\r')) s[--n] = 0;
        if (!n || s[0] == '#') continue;
        char* tab = strchr(s, '\t');
        if (!tab) continue;
        *tab = 0;
        g_quest[conv(s, CP_UTF8, 1252)] = conv(tab + 1, CP_UTF8, 949);
    }
    fclose(f);
    logf("quest literals: %u", (unsigned)g_quest.size());
}

static void fix_node(int* n) {
    if (!n || n[0] != 0x23 || !n[2]) return;
    const char* s = (const char*)n[2];
    auto it = g_quest.find(s);
    if (it == g_quest.end()) {
        if (g_debug && *s) {
            static std::unordered_map<std::string, int> miss;
            if (miss.size() < 20000 && miss.emplace(s, 1).second) logf("quest miss: %s", s);
        }
        return;
    }
    int len = (int)it->second.size() + 1;
    if (len > 32000) return;
    char* p = len < 0xDD ? (char*)((PoolAllocFn)A_POOL_ALLOC)(*(void**)0xA11BFC, 0, len)
                         : (char*)((OpNewFn)A_OPNEW)((unsigned)len);
    if (!p) return;
    memcpy(p, it->second.c_str(), len);
    n[2] = (int)p;   // the old buffer leaks; it is small and scripts load once
    n[3] = len;
    if (g_quest_hits++ < 3) logf("quest hit: %s", s);
}

static int* __cdecl h_node_file(void* a, int b, int c) { int* n = o_node_file(a, b, c); fix_node(n); return n; }
static int* __cdecl h_node_mem(void* a, int b, int c) { int* n = o_node_mem(a, b, c); fix_node(n); return n; }

static NodeFn make_tramp6(DWORD at) {
    BYTE* tr = (BYTE*)VirtualAlloc(nullptr, 16, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(tr, (void*)at, 6);  // mov ecx,[0A11BFCh]
    tr[6] = 0xE9;
    *(DWORD*)(tr + 7) = (at + 6) - (DWORD)(tr + 11);
    return (NodeFn)tr;
}

static void install_quest() {
    static const BYTE sig_a[] = {0x8B, 0x0D, 0xFC, 0x1B, 0xA1, 0x00, 0x83, 0xEC, 0x08};
    static const BYTE sig_b[] = {0x8B, 0x0D, 0xFC, 0x1B, 0xA1, 0x00, 0x53, 0x55, 0x56};
    if (memcmp((void*)A_NODE_FILE, sig_a, sizeof sig_a) || memcmp((void*)A_NODE_MEM, sig_b, sizeof sig_b)) {
        logf("quest loader signature mismatch");
        return;
    }
    load_quest();
    if (g_quest.empty() && !g_debug) return;
    o_node_file = make_tramp6(A_NODE_FILE);
    o_node_mem = make_tramp6(A_NODE_MEM);
    bool ok = patch_jmp(A_NODE_FILE, (void*)h_node_file) && patch_jmp(A_NODE_MEM, (void*)h_node_mem);
    logf("quest hooks: %s", ok ? "ok" : "FAILED");
}

// ------------------------------------------------------- file redirect ---
// The VFS opens loose files (game dir + name) before looking in packs, so a
// translated copy inside Korean.azp never wins over a loose original such as
// Quests\E1P\e6q.txt. Instead, any read of <game>\X is served from
// <game>\Korean\X when that file exists. Originals stay untouched.
static const DWORD A_FOPEN = 0x6BDC5A;   // FILE* fopen(path, mode)
static const DWORD A_FSOPEN = 0x6BDBFE;  // FILE* _fsopen(path, mode, shflag)
typedef void* (__cdecl* FsopenFn)(const char*, const char*, int);
static char g_gamedir[MAX_PATH];
static size_t g_gamedir_len;
static bool g_redirect;

static void* __cdecl h_fopen(const char* path, const char* mode) {
    const char* use = path;
    char alt[MAX_PATH * 2];
    if (g_redirect && path && mode && mode[0] == 'r') {
        const char* rel = nullptr;
        if (path[0] && path[1] == ':') {
            if (_strnicmp(path, g_gamedir, g_gamedir_len) == 0) rel = path + g_gamedir_len;
        } else {
            rel = path;
            while (rel[0] == '.' && (rel[1] == '\\' || rel[1] == '/')) rel += 2;
        }
        if (rel && _strnicmp(rel, "Korean\\", 7) != 0 &&
            _snprintf(alt, sizeof alt, "%sKorean\\%s", g_gamedir, rel) > 0) {
            alt[sizeof alt - 1] = 0;
            DWORD a = GetFileAttributesA(alt);
            if (a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY)) {
                use = alt;
                logf("redirect %s", rel);
            }
        }
    }
    return ((FsopenFn)A_FSOPEN)(use, mode, 0x40);
}

static void install_redirect() {
    static const BYTE sig_fopen[] = {0x6A, 0x40, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C, 0xE8};
    if (memcmp((void*)A_FOPEN, sig_fopen, sizeof sig_fopen)) { logf("fopen signature mismatch"); return; }
    GetModuleFileNameA(nullptr, g_gamedir, MAX_PATH);
    char* s = strrchr(g_gamedir, '\\');
    if (s) s[1] = 0;
    g_gamedir_len = strlen(g_gamedir);
    char kd[MAX_PATH];
    _snprintf(kd, sizeof kd, "%sKorean", g_gamedir);
    kd[sizeof kd - 1] = 0;
    DWORD a = GetFileAttributesA(kd);
    if (a == INVALID_FILE_ATTRIBUTES || !(a & FILE_ATTRIBUTE_DIRECTORY)) { logf("no Korean\\ folder, redirect off"); return; }
    g_redirect = true;
    logf("file redirect: %s", patch_jmp(A_FOPEN, (void*)h_fopen) ? "ok" : "FAILED");
}

static void install() {
    char exe[MAX_PATH];
    GetModuleFileNameA(nullptr, exe, MAX_PATH);
    const char* base = strrchr(exe, '\\');
    base = base ? base + 1 : exe;
    if (_stricmp(base, "EB.exe") != 0) return;

    static const BYTE sig_draw[] = {0x83, 0xEC, 0x34, 0x53, 0x55, 0x56, 0x8B, 0x74, 0x24, 0x44};
    static const BYTE sig_width[] = {0x8B, 0x4C, 0x24, 0x04, 0xD9, 0x05, 0x04, 0xB4, 0x6E, 0x00};
    if (memcmp((void*)A_DRAWSTRING, sig_draw, sizeof sig_draw) ||
        memcmp((void*)A_WIDTH, sig_width, sizeof sig_width)) {
        logf("EB.exe signature mismatch - not 1.11 b286, hooks not installed");
        return;
    }

    // trampoline: sub esp,34h / push ebx / push ebp ; jmp 685CD5
    BYTE* tr = (BYTE*)VirtualAlloc(nullptr, 16, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(tr, (void*)A_DRAWSTRING, 5);
    tr[5] = 0xE9;
    *(DWORD*)(tr + 6) = (A_DRAWSTRING + 5) - (DWORD)(tr + 10);
    o_DrawString = (DrawStringFn)tr;

    bool ok = patch_jmp(A_DRAWSTRING, (void*)h_DrawString) && patch_jmp(A_WIDTH, (void*)h_Width);
    logf("hooks installed: %s", ok ? "ok" : "FAILED");
    static const BYTE sig_add[] = {0x8B, 0x44, 0x24, 0x0C, 0x8B, 0x4C, 0x24, 0x10, 0x8B, 0x54, 0x24, 0x14};
    if (!memcmp((void*)A_ADDTEXT, sig_add, sizeof sig_add)) patch_jmp(A_ADDTEXT, (void*)h_AddText);
    static const BYTE sig_bmp[] = {0x8B, 0x44, 0x24, 0x0C, 0x83, 0xEC, 0x48, 0x8D, 0x50, 0x01};
    if (!memcmp((void*)A_TEXTBMP, sig_bmp, sizeof sig_bmp)) {
        BYTE* tb = (BYTE*)VirtualAlloc(nullptr, 16, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
        memcpy(tb, (void*)A_TEXTBMP, 7);
        tb[7] = 0xE9;
        *(DWORD*)(tb + 8) = (A_TEXTBMP + 7) - (DWORD)(tb + 12);
        o_TextBmp = (TextBmpFn)tb;
        logf("text-bitmap hook: %s", patch_jmp(A_TEXTBMP, (void*)h_TextBmp) ? "ok" : "FAILED");
    }
    static const BYTE sig_tip[] = {0x51, 0x57, 0x8B, 0x7C, 0x24, 0x10, 0x85, 0xFF};
    if (o_TextBmp && !memcmp((void*)A_TIPTEXT, sig_tip, sizeof sig_tip)) {
        BYTE* tb = (BYTE*)VirtualAlloc(nullptr, 16, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
        memcpy(tb, (void*)A_TIPTEXT, 6);
        tb[6] = 0xE9;
        *(DWORD*)(tb + 7) = (A_TIPTEXT + 6) - (DWORD)(tb + 11);
        o_TipText = (TipTextFn)tb;
        logf("tooltip hook: %s", patch_jmp(A_TIPTEXT, (void*)h_TipText) ? "ok" : "FAILED");
    }
    install_redirect();
    install_quest();
}

// Blue Sun (Steam) needs HLA.dll (Hard Life engine patches: item limits etc).
// Its launcher E6.exe/HLA.exe injects it and runs LibMain while the game is
// still paused; we reproduce that from DllMain, before EB.exe's main runs.
// Skipped when HLA.dll is already loaded (game started through the launcher).
static void load_hla() {
    char exe[MAX_PATH];
    GetModuleFileNameA(nullptr, exe, MAX_PATH);
    const char* b = strrchr(exe, '\\');
    if (_stricmp(b ? b + 1 : exe, "EB.exe") != 0) return;
    if (GetModuleHandleA("HLA.dll")) { logf("HLA.dll already loaded"); return; }
    char path[MAX_PATH];
    sprintf_s(path, "%s\\HLA.dll", g_dir);
    if (GetFileAttributesA(path) == INVALID_FILE_ATTRIBUTES) return;
    char flag[MAX_PATH];
    sprintf_s(flag, "%s\\kor_nohla.txt", g_dir);
    if (GetFileAttributesA(flag) != INVALID_FILE_ATTRIBUTES) { logf("HLA load disabled"); return; }
    HMODULE h = LoadLibraryA(path);
    if (!h) { logf("LoadLibrary HLA.dll failed: %lu", GetLastError()); return; }
    void* lm = (void*)GetProcAddress(h, "LibMain");
    if (!lm) { logf("HLA LibMain missing"); return; }
    __asm {
        mov esi, esp
        push 0
        call lm
        mov esp, esi
    }
    logf("HLA.dll LibMain done");
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        GetModuleFileNameA(h, g_dir, MAX_PATH);
        char* s = strrchr(g_dir, '\\');
        if (s) *s = 0;
        // optional bundled font: <game>\KoreanFont.ttf + face name in kor_font.txt
        char ttf[MAX_PATH];
        sprintf_s(ttf, "%s\\KoreanFont.ttf", g_dir);
        if (GetFileAttributesA(ttf) != INVALID_FILE_ATTRIBUTES) {
            int n = AddFontResourceExA(ttf, FR_PRIVATE, 0);
            char cfg[MAX_PATH];
            sprintf_s(cfg, "%s\\kor_font.txt", g_dir);
            FILE* fp = nullptr;
            if (n && !fopen_s(&fp, cfg, "rb") && fp) {
                char face[128] = {};
                fread(face, 1, sizeof face - 1, fp);
                fclose(fp);
                for (char* q = face; *q; q++) if (*q == '\r' || *q == '\n') *q = 0;
                MultiByteToWideChar(CP_UTF8, 0, face, -1, g_face, 64);
            }
        }
        char dbg[MAX_PATH];
        sprintf_s(dbg, "%s\\kor_debug.txt", g_dir);
        g_debug = GetFileAttributesA(dbg) != INVALID_FILE_ATTRIBUTES;
        load_subst();
        load_hla();
        install();
    }
    return TRUE;
}
