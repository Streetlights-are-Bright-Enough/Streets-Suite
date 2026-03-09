#include <kernel.h>
#include <debug.h>
#include <stdio.h>

int main(void) {
    init_scr();
    scr_printf("Laser Tester\n");

    FILE *f = fopen("cdfs:/SYSTEM.CNF;1", "rb");
    if (f) {
        unsigned char tmp[64];
        size_t n = fread(tmp, 1, sizeof(tmp), f);
        fclose(f);
        scr_printf("Disc read probe: PASS (%u bytes)\n", (unsigned int)n);
    } else {
        scr_printf("Disc read probe: FAIL (no disc / unreadable)\n");
    }

    while (1) {}
    return 0;
}
