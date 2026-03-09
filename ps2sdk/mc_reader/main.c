#include <kernel.h>
#include <debug.h>

int main(void) {
    init_scr();
    scr_printf("Memory Card Reader Tester\n");
    scr_printf("TODO: wire mcman/mcserv read-write probe for mc0:/ and mc1:/\n");
    scr_printf("Sanity: tester ELF boots and can be used for integration checks.\n");
    while (1) {}
    return 0;
}
