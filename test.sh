#!/usr/bin/env bash
# Run tests grouped by module with visual separators
set -e

MODULES=("dice" "character" "party" "monster" "combat" "tables" "encounter" "state")

for mod in "${MODULES[@]}"; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $mod"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cargo test "game::${mod}" -- --color=always 2>&1 | grep -E "^test |^running |^test result"
    echo ""
done
