#!/bin/sh
# The Battle Castle's rules, Platinum's own C against ours (notes/PLATINUM_FRONTIER.md "The Battle Castle").
#   b2tools/platinum_castle_host/run.sh [SEEDS]      (b2tools/platinum_castle_check.py runs this under a watchdog)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
OUT=${CASTLE_HOST_OUT:-${TMPDIR:-/tmp}/platinum_castle_host}
CC=${FRONTIER_CC:-/opt/homebrew/opt/llvm/bin/clang}
mkdir -p "$OUT"
python3 "$HERE/extract.py" "$OUT" >/dev/null
python3 "$ROOT/b2tools/platinum_frontier_data.py" --sets "$OUT/sets.blob"
python3 "$ROOT/b2tools/platinum_hall_data.py" --personal "$OUT/personal.bin"
FLAGS="-std=c11 -g -fsanitize=address,undefined -fno-sanitize-recover=all"
# Platinum's own text (its warnings are its own): its two-draw u32s shift a u16 left by 16 as an int, as the DS does; and
# FrontierPokemon_Init divides 510 by the set's EV flag count, which set 0 (the padding a resumed solo challenge loads as its
# fourth Pokemon) doesn't have: the quotient goes to no stat (no flag), arm64 gives 0 as the DS's divider does
for f in plat_castle plat_self_app plat_opponent_app; do
    $CC $FLAGS -fno-sanitize=shift,integer-divide-by-zero -Wno-everything -I"$HERE" -I"$OUT" -c -o "$OUT/$f.o" "$OUT/$f.c"
done
# Ours, as the decomp has it (PearlB2's src/pokebw2 copy), against the harness's stand-ins for types.h and pearlb2.h
$CC $FLAGS -DPEARLB2_HOST -Wall -Wextra -Werror -I"$HERE/b2" -I"$ROOT/src/pokebw2/include" -c -o "$OUT/castle_rules.o" \
    "$ROOT/src/pokebw2/src/pearlb2/plat_castle/castle_rules.c"
$CC $FLAGS -Wall -Wextra -Wno-unused-parameter -Wno-sign-compare -Wno-missing-field-initializers -I"$HERE" -I"$OUT" -I"$HERE/b2" \
    -I"$ROOT/src/pokebw2/include" -c -o "$OUT/sim.o" "$HERE/sim.c"
$CC $FLAGS -o "$OUT/sim" "$OUT/sim.o" "$OUT/plat_castle.o" "$OUT/plat_self_app.o" "$OUT/plat_opponent_app.o" "$OUT/castle_rules.o"
"$OUT/sim" "$OUT/sets.blob" "$OUT/personal.bin" "$@"
