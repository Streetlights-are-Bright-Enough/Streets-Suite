#include <kernel.h>
#include <gsKit.h>
#include <dmaKit.h>

int main(void) {
    dmaKit_init(D_CTRL_RELE_OFF, D_CTRL_MFD_OFF, D_CTRL_STS_UNSPEC, D_CTRL_STD_OFF, D_CTRL_RCYC_8, 1 << DMA_CHANNEL_GIF);
    dmaKit_chan_init(DMA_CHANNEL_GIF);

    GSGLOBAL *gs = gsKit_init_global();
    gs->PSM = GS_PSM_CT24;
    gs->PSMZ = GS_PSMZ_16S;
    gsKit_init_screen(gs);
    gsKit_mode_switch(gs, GS_ONESHOT);

    u64 c0 = GS_SETREG_RGBAQ(0xff, 0x00, 0x00, 0x80, 0x00);
    u64 c1 = GS_SETREG_RGBAQ(0x00, 0xff, 0x00, 0x80, 0x00);
    u64 c2 = GS_SETREG_RGBAQ(0x00, 0x00, 0xff, 0x80, 0x00);

    while (1) {
        gsKit_clear(gs, GS_SETREG_RGBAQ(0x00, 0x00, 0x00, 0x80, 0x00));
        gsKit_prim_sprite(gs, 40, 40, 280, 200, 1, c0);
        gsKit_prim_sprite(gs, 300, 40, 540, 200, 1, c1);
        gsKit_prim_sprite(gs, 180, 220, 460, 420, 1, c2);
        gsKit_sync_flip(gs);
        gsKit_queue_exec(gs);
    }

    return 0;
}
