#!/bin/sh
# The Battle Factory's rules, Platinum's own C against the code the ROM runs (notes/PLATINUM_FRONTIER.md "The Battle Factory").
#   b2tools/platinum_factory_host/run.sh [SEEDS]       (b2tools/platinum_frontier_check.py runs this under a watchdog)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
OUT=${FACTORY_HOST_OUT:-${TMPDIR:-/tmp}/platinum_factory_host}
CC=${FRONTIER_CC:-/opt/homebrew/opt/llvm/bin/clang}
OURS=$ROOT/src/pokebw2
[ -f "$OURS/src/pearlb2/plat_factory/factory_rules.c" ] || OURS=$ROOT/external/pokebw2
mkdir -p "$OUT"
python3 "$HERE/extract.py" "$OUT" >/dev/null
python3 "$HERE/../platinum_frontier_data.py" --sets "$OUT/sets.blob"
python3 "$HERE/species.py" "$OUT/species.blob"
FLAGS="-std=c11 -DPEARLB2_HOST -g -fsanitize=address,undefined -fno-sanitize-recover=all"
# Platinum's own text (its warnings are its own). It shifts a u16 random number left by 16 as an int, as the DS does; and
# FrontierPokemon_Init divides 510 by the set's EV flag count, which set 0 (the padding a resumed solo challenge loads as its
# fourth Pokemon) doesn't have: the quotient goes to no stat (no flag), arm64 gives 0 as the DS's divider does
$CC $FLAGS -fno-sanitize=shift,integer-divide-by-zero -Wno-everything -I"$OUT" -I"$HERE" -c -o "$OUT/plat_factory.o" "$OUT/plat_factory.c"
# Ours, as the overlay has it, with the decomp's types from b2types/
$CC $FLAGS -Wall -Wextra -I"$HERE/b2types" -I"$OURS/include" -c -o "$OUT/factory_rules.o" "$OURS/src/pearlb2/plat_factory/factory_rules.c"
$CC $FLAGS -Wall -Wextra -Wno-missing-field-initializers -I"$OUT" -I"$HERE" -I"$HERE/b2types" -I"$OURS/include" -c -o "$OUT/sim.o" "$HERE/sim.c"
$CC $FLAGS -o "$OUT/sim" "$OUT/sim.o" "$OUT/plat_factory.o" "$OUT/factory_rules.o"
"$OUT/sim" "$OUT/sets.blob" "$OUT/species.blob" "${1:-200}"
