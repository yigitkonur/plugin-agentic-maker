#!/bin/sh
# Pre-release gate: the release workflow runs this on the bumped tree. It is the repo's full local gate.
set -eu
cd "$(dirname "$0")/.."
exec sh scripts/check.sh
