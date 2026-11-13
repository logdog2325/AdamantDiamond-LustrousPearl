#!/bin/sh
# The Battle Hall's rules, Platinum's own C against ours (notes/PLATINUM_FRONTIER.md "The Battle Hall").
#   b2tools/platinum_hall_host/run.sh [SEEDS]      (b2tools/platinum_hall_check.py runs this under a watchdog)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
OUT=${HALL_HOST_OUT:-${TMPDIR:-/tmp}/platinum_hall_host}
CC=${FRONTIER_CC:-/opt/homebrew/opt/llvm/bin/clang}
mkdir -p "$OUT"
python3 "$HERE/extract.py" "$OUT" >/dev/null
python3 "$ROOT/b2tools/platinum_hall_data.py" --table "$OUT/table.bin" >/dev/null
python3 "$ROOT/b2tools/platinum_hall_data.py" --personal "$OUT/personal.bin"
python3 "$ROOT/b2tools/platinum_frontier_data.py" --sets "$OUT/trainers.bin"
python3 "$ROOT/b2tools/platinum_hall_data.py" --names "$OUT/names.bin"
FLAGS="-std=c11 -g -fsanitize=address,undefined -fno-sanitize-recover=all"
# Platinum's own text (its warnings are its own): its two-draw u32s shift a u16 left by 16 as an int, set 0 (no EVs) divides 510
# by 0 (FrontierPokemon_Init; the ARM's division routine returns, and no stat takes the result), and its AI test for Argenta reads
# trainerIDs[currentBattle * 4], past the array from the 6th battle on, into opponents[0] (laid out as on the DS: offsets 24 and
# 64 here too): those three checks are off
$CC $FLAGS -fno-sanitize=shift,integer-divide-by-zero,bounds -Wno-everything -I"$HERE" -I"$OUT" -c -o "$OUT/plat_rules.o" "$OUT/plat_rules.c"
# Ours, as the decomp has it (PearlB2's src/pokebw2 copy), against the harness's stand-ins for types.h and pearlb2.h
$CC $FLAGS -Wall -Wextra -Werror -I"$HERE/b2" -I"$ROOT/src/pokebw2/include" -c -o "$OUT/hall_rules.o" \
    "$ROOT/src/pokebw2/src/pearlb2/plat_hall/hall_rules.c"
$CC $FLAGS -Wall -Wextra -Wno-unused-parameter -Wno-sign-compare -I"$HERE" -I"$OUT" -I"$HERE/b2" -I"$ROOT/src/pokebw2/include" -c -o "$OUT/sim.o" "$HERE/sim.c"
$CC $FLAGS -o "$OUT/sim" "$OUT/sim.o" "$OUT/plat_rules.o" "$OUT/hall_rules.o"
"$OUT/sim" "$OUT/table.bin" "$OUT/personal.bin" "$OUT/trainers.bin" "$OUT/names.bin" "$@"
