#!/bin/sh
# The Distortion World's harness (notes/PLATINUM_DW.md): Platinum's own C beside dw_core.c, route by route.
#   b2tools/platinum_dw_host/run.sh ROUTES [TRACE]     (b2tools/platinum_dw_check.py writes ROUTES and runs this)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
OUT=${DW_HOST_OUT:-${TMPDIR:-/tmp}/platinum_dw_host}
D=${DW_DECOMP:-$ROOT/external/pokebw2}
P=$ROOT/external/pokeplatinum
CC=${DW_CC:-/opt/homebrew/opt/llvm/bin/clang}
mkdir -p "$OUT/inc/pearlb2"
cp "$D/include/pearlb2/plat_dw.h" "$OUT/inc/pearlb2/"
python3 "$HERE/extract.py" "$OUT/plat_extract.c" >/dev/null
python3 "$ROOT/b2tools/platinum_dw_data.py" --blob "$OUT/dw.blob" >/dev/null
python3 "$ROOT/b2tools/platinum_dw_data.py" --narcs "$OUT" >/dev/null
FLAGS="-std=c23 -g -fsanitize=address,undefined -fno-sanitize-recover=all"
# Platinum's side: its own C, as written (its warnings are its own). Its file sections are structs with a pointer after
# the count (DistWorldMapFileFloatingPlatformSection), which the code reads at offset 0 only: 8-byte pointers on the Mac
# make the cast misaligned, harmless there, so the alignment check is off for this file alone; and it shifts negative
# numbers left (the elevators' paths: (offset << 4) * FX32_ONE), which the DS's ARM does as a multiply, so the shift
# check is off for it too
$CC $FLAGS -fno-sanitize=alignment,shift -Wno-everything -I"$HERE" -I"$OUT" -I"$P/include" -c -o "$OUT/plat_shim.o" "$HERE/plat_shim.c"
# Ours: the overlay's file
$CC $FLAGS -Wall -Wextra -Wno-unused-parameter -DDW_HOST -I"$HERE" -I"$OUT/inc" -c -o "$OUT/dw_core.o" "$D/src/pearlb2/plat_dw/dw_core.c"
$CC $FLAGS -Wall -Wextra -Wno-unused-parameter -DDW_HOST -I"$HERE" -I"$OUT/inc" -c -o "$OUT/b2_side.o" "$HERE/b2_side.c"
$CC $FLAGS -Wall -Wextra -I"$HERE" -c -o "$OUT/sim.o" "$HERE/sim.c"
$CC $FLAGS -o "$OUT/sim" "$OUT/sim.o" "$OUT/plat_shim.o" "$OUT/dw_core.o" "$OUT/b2_side.o"
"$OUT/sim" "$OUT/tw_arc.narc" "$OUT/tw_arc_attr.narc" "$OUT/dw.blob" "$@"
