# D

## PS2 suite

Main entry: `ps2_suite.py`

### What tests it has now
The suite includes named diagnostic slots for:
- gamepad tester
- RAM tester
- VRAM tester
- GPU tester
- CPU tester
- memory card reader
- laser tester

Run:
```bash
python3 ps2_suite.py list-tests
```

### Core commands
```bash
python3 ps2_suite.py validate-config --config ps2_config.example.json
python3 ps2_suite.py inventory --config ps2_config.example.json
python3 ps2_suite.py smoke --config ps2_config.example.json --report ps2_report.md
python3 ps2_suite.py diag --config ps2_config.example.json --report ps2_diag_report.md
python3 ps2_suite.py diag --config ps2_config.example.json --report ps2_diag_report.md --debug
python3 ps2_suite.py diag --config ps2_config.example.json --report ps2_diag_report.md --allow-missing
```

### Sanity check: the warning/non-zero `diag` exit
If you run `diag` with placeholder paths from `ps2_config.example.json`, it should return non-zero.
That is expected and means targets were configured but not found / not passing.

Current behavior (default strict mode):
- exit `1`: no diagnostic targets configured
- exit `2`: one or more configured targets failed
- exit `0`: all configured targets passed

Debug/sanity options:
- `--debug` prints one line per diagnostic with configured/pass/note state
- `--allow-missing` forces exit `0` so you can verify plumbing/report generation even with placeholder paths

### How `diag` works
- `diagnostic_targets` maps each named test to a file path.
- If target is `.elf`, it boots in `elf` mode.
- Otherwise it boots in `disc` mode.
- Missing targets are reported as failed with a clear note in the report.

This gives you one report that shows which requested checks are wired and whether each one boot-smoked successfully under PCSX2.

## Build a PS2 `.ELF` (PS2SDK) + Makefile

`ps2_suite.py` is host-side only. To run on console (FreeMcBoot/uLaunchELF), build each tester as a PS2 `.ELF`.

### Example minimal Makefile (PS2SDK)
Use this in your PS2 homebrew tester project:

```make
EE_BIN = tester.elf
EE_OBJS = main.o
EE_LIBS =
EE_INCS =
EE_CFLAGS += -O2 -G0 -Wall

all: $(EE_BIN)

clean:
	rm -f $(EE_OBJS) $(EE_BIN)

include $(PS2SDK)/samples/Makefile.pref
include $(PS2SDK)/samples/Makefile.eeglobal
```

### Build steps
```bash
make clean
make
```

Optional pack step:
```bash
ee-strip tester.elf
ps2-packer tester.elf tester-packed.elf
```



### Included PS2SDK tester sources
Concrete starter tester projects are included for every requested category:
- `ps2sdk/gamepad_tester/`
- `ps2sdk/ram_tester/`
- `ps2sdk/vram_tester/`
- `ps2sdk/gpu_tester/`
- `ps2sdk/cpu_tester/`
- `ps2sdk/mc_reader/`
- `ps2sdk/laser_tester/`

Build any tester:
```bash
cd ps2sdk/<tester_name>
make clean
make
```

Build all included suites at once:
```bash
bash ps2sdk/build_all.sh
```

Then run sanity + debug against the existing suites:
```bash
python3 ps2_suite.py diag --config ps2_config.example.json --report ps2_diag_report.md --debug
```

If you only want plumbing validation while suites are still missing/not built:
```bash
python3 ps2_suite.py diag --config ps2_config.example.json --report ps2_diag_report.md --debug --allow-missing
```

### Included GPU polygon phrase tester source
A concrete PS2SDK GPU test source is included at:
- `ps2sdk/gpu_tester/main.c`
- `ps2sdk/gpu_tester/Makefile`

It renders polygon/block letters that spell:
- `FAT`
- `CUNT`

Build it with PS2SDK:
```bash
cd ps2sdk/gpu_tester
make clean
make
```

The example config already points `gpu_tester` to `./ps2sdk/gpu_tester/gpu_tester.elf`, so once built it is picked up automatically by `diag`.

### Use with this suite
- The example config targets local outputs under `./ps2sdk/<tester>/<tester>.elf`.
- Re-run after build:
```bash
python3 ps2_suite.py diag --config ps2_config.example.json --report ps2_diag_report.md
```
- Then copy those ELFs to USB/MC for FreeMcBoot launch on official hardware.
