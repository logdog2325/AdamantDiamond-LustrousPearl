#!/bin/sh
# (plat-dw-finish) The boulder puzzle's harness: Platinum's C beside dw_core.c.  boulder.sh [-v]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
OUT=${DW_HOST_OUT:-${TMPDIR:-/tmp}/platinum_dw_host}/boulder
D=${DW_DECOMP:-$ROOT/external/pokebw2}
P=$ROOT/external/pokeplatinum
CC=${DW_CC:-/opt/homebrew/opt/llvm/bin/clang}
mkdir -p "$OUT/inc/pearlb2"
cp "$D/include/pearlb2/plat_dw.h" "$OUT/inc/pearlb2/"
python3 "$HERE/extract.py" --boulder "$OUT/plat_boulder_extract.c" >/dev/null
python3 "$ROOT/b2tools/platinum_dw_data.py" --blob "$OUT/dw.blob" >/dev/null
python3 -c "import sys; sys.path.insert(0, '$ROOT/b2tools'); import platinum_dw_world as w; open('$OUT/world.blob', 'wb').write(w.world_blob())"
FLAGS="-std=c23 -g -fsanitize=address,undefined -fno-sanitize-recover=all"
$CC $FLAGS -Wno-everything -I"$HERE" -I"$OUT" -c -o "$OUT/boulder_shim.o" "$HERE/boulder_shim.c"
$CC $FLAGS -Wall -Wextra -Wno-unused-parameter -DDW_HOST -I"$HERE" -I"$OUT/inc" -c -o "$OUT/dw_core.o" "$D/src/pearlb2/plat_dw/dw_core.c"
$CC $FLAGS -Wall -Wextra -Wno-unused-parameter -DDW_HOST -I"$HERE" -I"$OUT/inc" -c -o "$OUT/b2_boulder.o" "$HERE/b2_boulder.c"
$CC $FLAGS -Wall -Wextra -I"$HERE" -c -o "$OUT/boulder_sim.o" "$HERE/boulder_sim.c"
$CC $FLAGS -o "$OUT/boulder_sim" "$OUT/boulder_sim.o" "$OUT/boulder_shim.o" "$OUT/dw_core.o" "$OUT/b2_boulder.o"
"$OUT/boulder_sim" "$OUT/dw.blob" "$OUT/world.blob" "$@"
