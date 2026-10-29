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
#           texinfo (makeinfo), gettext (msgfmt), glib-2.0 development headers.
#   Debian/Ubuntu: apt-get install build-essential autoconf automake pkg-config \
#                  bison flex texinfo gettext libglib2.0-dev
set -euo pipefail

for tool in git gcc make autoreconf automake pkg-config bison flex makeinfo msgfmt; do
  command -v "$tool" >/dev/null 2>&1 || { echo "build-gnubg: missing required tool: $tool" >&2; exit 1; }
done
pkg-config --exists glib-2.0 || { echo "build-gnubg: missing glib-2.0 development headers" >&2; exit 1; }

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
