EE_BIN = laser_tester.elf
EE_OBJS = main.o
EE_CFLAGS += -O2 -G0 -Wall
EE_LIBS += -lpatches

all: $(EE_BIN)

clean:
	rm -f $(EE_OBJS) $(EE_BIN)

include $(PS2SDK)/samples/Makefile.pref
include $(PS2SDK)/samples/Makefile.eeglobal
