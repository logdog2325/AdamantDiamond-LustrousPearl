#!/bin/sh
# The Battle Arcade's rules, Platinum's own C against ours (notes/PLATINUM_FRONTIER.md "The Battle Arcade").
#   b2tools/platinum_arcade_host/run.sh [SEEDS]      (b2tools/platinum_arcade_check.py runs this under a watchdog)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
OUT=${ARCADE_HOST_OUT:-${TMPDIR:-/tmp}/platinum_arcade_host}
CC=${FRONTIER_CC:-/opt/homebrew/opt/llvm/bin/clang}
mkdir -p "$OUT"
python3 "$HERE/extract.py" "$OUT" >/dev/null
python3 "$ROOT/b2tools/platinum_frontier_data.py" --sets "$OUT/sets.blob"
python3 "$ROOT/b2tools/platinum_arcade_data.py" --personal "$OUT/personal.bin"
FLAGS="-std=c11 -g -fsanitize=address,undefined -fno-sanitize-recover=all"
# Platinum's own text (its warnings are its own): its two-draw u32s shift a u16 left by 16 as an int, as the DS does; and
# FrontierPokemon_Init divides 510 by the set's EV flag count, which set 0 (the padding a resumed solo challenge loads as its
# fourth Pokemon) doesn't have: the quotient goes to no stat (no flag)
for f in plat_arcade plat_app; do
    $CC $FLAGS -fno-sanitize=shift,integer-divide-by-zero,float-cast-overflow -Wno-everything -I"$HERE" -I"$OUT" -c \
        -o "$OUT/$f.o" "$OUT/$f.c"
done
# Ours, as the decomp has it (PearlB2's src/pokebw2 copy), against the harness's stand-ins for types.h and pearlb2.h (the
# Castle's)
$CC $FLAGS -DPEARLB2_HOST -Wall -Wextra -Werror -I"$ROOT/b2tools/platinum_castle_host/b2" -I"$ROOT/src/pokebw2/include" -c \
    -o "$OUT/arcade_rules.o" "$ROOT/src/pokebw2/src/pearlb2/plat_arcade/arcade_rules.c"
$CC $FLAGS -Wall -Wextra -Wno-unused-parameter -Wno-sign-compare -Wno-missing-field-initializers -I"$HERE" -I"$OUT" \
    -I"$ROOT/b2tools/platinum_castle_host/b2" -I"$ROOT/src/pokebw2/include" -c -o "$OUT/sim.o" "$HERE/sim.c"
$CC $FLAGS -o "$OUT/sim" "$OUT/sim.o" "$OUT/plat_arcade.o" "$OUT/plat_app.o" "$OUT/arcade_rules.o"
"$OUT/sim" "$OUT/sets.blob" "$OUT/personal.bin" "$@"
