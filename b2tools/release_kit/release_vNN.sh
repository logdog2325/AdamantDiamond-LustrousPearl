#!/bin/zsh
# Release template (from HoennB2's release kit, made generic): build a clean commit, make the .bps, copy release files.
# Usage: zsh release_vNN.sh <commit> <version, e.g. 1.0>
# Not adapted to Pearl yet: the build step is a placeholder until PearlB2's build pipeline exists (notes/PLAN.md).
set -e -o pipefail
C=$1; V=$2
[[ -n "$C" && -n "$V" ]] || { echo "usage: release_vNN.sh <commit> <version>"; exit 1; }
ROOT=${0:a:h:h:h}
REL=$ROOT/release
cd $ROOT
git status --short | grep -v '^??' && { echo "worktree not clean"; exit 1; } || true
git checkout -q --detach $C
git log --oneline -1
df -h / | tail -1
for GAME in pearl:Pokemon_Lustrous_Pearl diamond:Pokemon_Adamant_Diamond; do
  VER=${GAME%%:*}; STEM=${GAME##*:}      # version.py VERSION, RELEASE_STEM
  ROM=work/rom$([[ $VER == diamond ]] && echo _diamond)/$VER.nds
  echo "== build $VER"; PEARL_VERSION=$VER nice python3 b2tools/build_rom.py --clean   # TODO(Pearl): the full patch list, once it exists
  mkdir -p $REL
  cp -c $ROM $REL/${STEM}_v$V.nds
  (cd b2tools && python3 bps.py make ../roms/black2_original.nds ../$ROM $REL/${STEM}_v$V.bps)
  shasum $REL/${STEM}_v$V.*
done
echo "Release files are in release/. Publishing is the user's call (ask first)."
