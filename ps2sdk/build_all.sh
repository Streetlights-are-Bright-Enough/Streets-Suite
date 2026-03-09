#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGETS=(
  gamepad_tester
  ram_tester
  vram_tester
  gpu_tester
  cpu_tester
  mc_reader
  laser_tester
)

for t in "${TARGETS[@]}"; do
  echo "[build] $t"
  make -C "$ROOT/$t" clean all

done

echo "Done. ELF outputs are in ps2sdk/<tester>/<tester>.elf"
