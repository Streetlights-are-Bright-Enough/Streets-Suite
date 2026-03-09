#include <kernel.h>
#include <debug.h>

int main(void) {
    init_scr();
    scr_printf("Gamepad Tester\n");
    scr_printf("TODO: wire libpad polling + button matrix output\n");
    scr_printf("Sanity: tester ELF boots on hardware/emulator.\n");
    while (1) {
        // keep screen alive for manual verification
    }
    return 0;
}
