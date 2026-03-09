#include <kernel.h>
#include <gsKit.h>
#include <dmaKit.h>

// Polygon-based GPU smoke scene:
// draws block letters to spell: FAT CUNT

typedef struct {
    float x;
    float y;
    float w;
    float h;
} Rect;

static void draw_rect(GSGLOBAL *gs, Rect r, u64 color) {
    gsKit_prim_sprite(gs, r.x, r.y, r.x + r.w, r.y + r.h, 1, color);
}

static void draw_F(GSGLOBAL *gs, float x, float y, float s, u64 c) {
    draw_rect(gs, (Rect){x, y, s, s * 5}, c);
    draw_rect(gs, (Rect){x, y, s * 3, s}, c);
    draw_rect(gs, (Rect){x, y + s * 2, s * 2.4f, s}, c);
}

static void draw_A(GSGLOBAL *gs, float x, float y, float s, u64 c) {
    draw_rect(gs, (Rect){x, y, s, s * 5}, c);
    draw_rect(gs, (Rect){x + s * 2, y, s, s * 5}, c);
    draw_rect(gs, (Rect){x, y, s * 3, s}, c);
    draw_rect(gs, (Rect){x, y + s * 2, s * 3, s}, c);
}

static void draw_T(GSGLOBAL *gs, float x, float y, float s, u64 c) {
    draw_rect(gs, (Rect){x, y, s * 3, s}, c);
    draw_rect(gs, (Rect){x + s, y, s, s * 5}, c);
}

static void draw_C(GSGLOBAL *gs, float x, float y, float s, u64 c) {
    draw_rect(gs, (Rect){x, y, s, s * 5}, c);
    draw_rect(gs, (Rect){x, y, s * 3, s}, c);
    draw_rect(gs, (Rect){x, y + s * 4, s * 3, s}, c);
}

static void draw_U(GSGLOBAL *gs, float x, float y, float s, u64 c) {
    draw_rect(gs, (Rect){x, y, s, s * 5}, c);
    draw_rect(gs, (Rect){x + s * 2, y, s, s * 5}, c);
    draw_rect(gs, (Rect){x, y + s * 4, s * 3, s}, c);
}

static void draw_N(GSGLOBAL *gs, float x, float y, float s, u64 c) {
    draw_rect(gs, (Rect){x, y, s, s * 5}, c);
    draw_rect(gs, (Rect){x + s * 2, y, s, s * 5}, c);
    // middle diagonal approximated by stepped blocks
    draw_rect(gs, (Rect){x + s, y + s, s, s}, c);
    draw_rect(gs, (Rect){x + s, y + s * 2, s, s}, c);
    draw_rect(gs, (Rect){x + s, y + s * 3, s, s}, c);
}

static void draw_word(GSGLOBAL *gs, const char *word, float x, float y, float s, u64 c) {
    for (int i = 0; word[i] != '\0'; ++i) {
        switch (word[i]) {
            case 'F': draw_F(gs, x, y, s, c); break;
            case 'A': draw_A(gs, x, y, s, c); break;
            case 'T': draw_T(gs, x, y, s, c); break;
            case 'C': draw_C(gs, x, y, s, c); break;
            case 'U': draw_U(gs, x, y, s, c); break;
            case 'N': draw_N(gs, x, y, s, c); break;
            default: break;
        }
        x += s * 4;
    }
}

int main(void) {
    dmaKit_init(D_CTRL_RELE_OFF, D_CTRL_MFD_OFF, D_CTRL_STS_UNSPEC, D_CTRL_STD_OFF, D_CTRL_RCYC_8, 1 << DMA_CHANNEL_GIF);
    dmaKit_chan_init(DMA_CHANNEL_GIF);

    GSGLOBAL *gs = gsKit_init_global();
    gs->PSM = GS_PSM_CT24;
    gs->PSMZ = GS_PSMZ_16S;
    gs->ZBuffering = GS_SETTING_ON;

    gsKit_init_screen(gs);
    gsKit_mode_switch(gs, GS_ONESHOT);

    u64 bg = GS_SETREG_RGBAQ(0x10, 0x10, 0x20, 0x80, 0x00);
    u64 fg = GS_SETREG_RGBAQ(0xff, 0xff, 0xff, 0x80, 0x00);

    while (1) {
        gsKit_clear(gs, bg);

        // Draw words as polygon blocks
        draw_word(gs, "FAT", 120.0f, 120.0f, 20.0f, fg);
        draw_word(gs, "CUNT", 120.0f, 280.0f, 20.0f, fg);

        gsKit_sync_flip(gs);
        gsKit_queue_exec(gs);
    }

    return 0;
}
