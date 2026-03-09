#include <kernel.h>
#include <debug.h>
#include <stdint.h>

int main(void) {
    uint32_t acc = 0x12345678u;
    init_scr();
    scr_printf("CPU Tester\n");

    for (uint32_t i = 0; i < 20000000u; ++i) {
        acc ^= (i * 1664525u) + 1013904223u;
        acc = (acc << 5) | (acc >> 27);
    }

    scr_printf("Stress hash: %08x\n", acc);
    scr_printf("If stable and not crashing, CPU path is sane.\n");
    while (1) {}
    return 0;
}
