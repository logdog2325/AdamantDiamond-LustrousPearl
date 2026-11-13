#!/bin/sh
# The Battle Tower's rules, Platinum's own C against the code the ROM runs (notes/PLATINUM_FRONTIER.md "The harness").
#   b2tools/platinum_frontier_host/run.sh [SEEDS]       (b2tools/platinum_frontier_check.py runs this under a watchdog)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${FRONTIER_HOST_OUT:-${TMPDIR:-/tmp}/platinum_frontier_host}
CC=${FRONTIER_CC:-/opt/homebrew/opt/llvm/bin/clang}
mkdir -p "$OUT"
python3 "$HERE/extract.py" "$OUT" >/dev/null
python3 "$HERE/../platinum_frontier_data.py" --sets "$OUT/sets.blob"
FLAGS="-std=c11 -g -fsanitize=address,undefined -fno-sanitize-recover=all -I$HERE"
# The decomps' own text (their warnings are their own). Both shift a u16 random number left by 16 as an int (the team's
# trainer id: random | random << 16), which the DS's ARM does as a plain shift: the shift check is off for these two files
$CC $FLAGS -fno-sanitize=shift -Wno-everything -c -o "$OUT/plat_rules.o" "$OUT/plat_rules.c"
$CC $FLAGS -fno-sanitize=shift -Wno-everything -c -o "$OUT/b2_rules.o" "$OUT/b2_rules.c"
$CC $FLAGS -Wall -Wextra -c -o "$OUT/sim.o" "$HERE/sim.c"
$CC $FLAGS -o "$OUT/sim" "$OUT/sim.o" "$OUT/plat_rules.o" "$OUT/b2_rules.o"
"$OUT/sim" "$OUT/sets.blob" "$@"
