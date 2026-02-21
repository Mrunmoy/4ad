#!/usr/bin/env bash
# Run tests grouped by module with visual separators
set -e

GAME_MODULES=("dice" "character" "party" "monster" "combat" "tables" "encounter" "state")
MAP_MODULES=("grid" "room" "dungeon")

for mod in "${GAME_MODULES[@]}"; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $mod"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cargo test "game::${mod}" -- --color=always 2>&1 | grep -E "^test |^running |^test result"
    echo ""
done

for mod in "${MAP_MODULES[@]}"; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $mod"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cargo test "map::${mod}" -- --color=always 2>&1 | grep -E "^test |^running |^test result"
    echo ""
done
