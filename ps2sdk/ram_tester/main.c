#include <kernel.h>
#include <debug.h>
#include <stdint.h>

int main(void) {
    static uint32_t buf[4096];
    uint32_t ok = 1;

    init_scr();
    scr_printf("RAM Tester\n");

    for (uint32_t i = 0; i < 4096; ++i) buf[i] = 0xA5A50000u ^ i;
    for (uint32_t i = 0; i < 4096; ++i) if (buf[i] != (0xA5A50000u ^ i)) ok = 0;

    scr_printf("Pattern test: %s\n", ok ? "PASS" : "FAIL");
    while (1) {}
    return 0;
}
