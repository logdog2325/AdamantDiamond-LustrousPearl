#!/bin/sh
# The rules of Pearl's Super Contests on the host: AI-only contests with the sanitizers on (notes/CONTESTS.md).
set -e
TOOLS=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(cd "$TOOLS/.." && pwd)
OUT=${CONTEST_HOST_OUT:-${TMPDIR:-/tmp}/contest_host}
D=$ROOT/external/pokebw2
mkdir -p "$OUT/inc/pearlb2"
cp "$D/include/pearlb2/contest.h" "$D/include/pearlb2/contest_port.h" "$OUT/inc/pearlb2/"
python3 "$TOOLS/contest_data.py" blob "$OUT/contest.blob" >/dev/null
clang -std=c99 -Wall -Wextra -Wno-unused-parameter -fsanitize=address,undefined -fno-sanitize-recover=all -g -DCONTEST_HOST \
    -I"$OUT/inc" -I"$D/src/pearlb2/contest" -o "$OUT/sim" "$TOOLS/contest_host/sim.c" "$D/src/pearlb2/contest/contest_rules.c"
"$OUT/sim" "$OUT/contest.blob" "${1:-20000}"
# Poffins: the rules, the stirring, the feeding (notes/CONTESTS.md)
cp "$D/include/pearlb2/poffin.h" "$OUT/inc/pearlb2/"
clang -std=c99 -Wall -Wextra -Wno-unused-parameter -fsanitize=address,undefined -fno-sanitize-recover=all -g -DCONTEST_HOST \
    -I"$OUT/inc" -I"$D/src/pearlb2/resident" -o "$OUT/poffin_sim" "$TOOLS/contest_host/poffin_sim.c" "$D/src/pearlb2/resident/poffin_rules.c"
"$OUT/poffin_sim"
