#!/usr/bin/env bash
# Build the GNU Backgammon command-line binary from source, without GTK.
#
# The `gnubg` Python wheel gives fast in-process evaluation, but its rollout
# command is a no-op, so rollouts run through the real binary built here.
#
# Usage: scripts/build-gnubg.sh [install-prefix]
#   default prefix: <repo>/.gnubg  (gitignored)
#
# Requires: git, gcc, make, autoconf, automake, pkg-config, bison, flex,
#           glib-2.0 development headers.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFIX="${1:-$REPO_ROOT/.gnubg}"
BUILD_DIR="${GNUBG_BUILD_DIR:-$REPO_ROOT/.gnubg-build}"
SRC_URL="${GNUBG_SRC_URL:-https://github.com/StonesAndDice/gnubg}"
JOBS="$(nproc 2>/dev/null || echo 2)"

mkdir -p "$BUILD_DIR"
if [ ! -d "$BUILD_DIR/src/.git" ]; then
  git clone --depth 1 "$SRC_URL" "$BUILD_DIR/src"
fi
cd "$BUILD_DIR/src"

autoreconf -fi
./configure \
  --prefix="$PREFIX" \
  --without-gtk \
  --without-python \
  --disable-cputest
make -j"$JOBS"
make install

echo
echo "Built: $PREFIX/bin/gnubg"
"$PREFIX/bin/gnubg" --version | head -1
