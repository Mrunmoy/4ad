"""Campaign persistence layer for 4AD.

Handles saving and loading campaign state between dungeon runs using SQLite.
All characters heal between dungeons (rulebook p.67), spells/abilities reset,
but equipment, gold, and level persist.

Barbarian rage does NOT reset between dungeons (once per campaign).
"""
import sqlite3
import json
import uuid
import os
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass
from contextlib import contextmanager

from src.character import (
    Character, Warrior, Cleric, Rogue, Wizard,
    Barbarian, Elf, Dwarf, Halfling,
    CHARACTER_CLASSES, create_character,
)
from src.equipment import Inventory


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dungeons_completed INTEGER DEFAULT 0,
    total_gold_earned INTEGER DEFAULT 0,
    total_monsters_killed INTEGER DEFAULT 0,
    total_rooms_explored INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS campaign_characters (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    class_type TEXT NOT NULL,
    level INTEGER DEFAULT 1,
    life INTEGER NOT NULL,
    max_life INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    gold INTEGER DEFAULT 0,
    equipment TEXT DEFAULT '[]',
    inventory_json TEXT DEFAULT '{}',
    spells_known TEXT DEFAULT '[]',
    spells_remaining INTEGER DEFAULT 0,
    healing_remaining INTEGER DEFAULT 0,
    rage_available BOOLEAN DEFAULT 1,
    luck_points INTEGER DEFAULT 0,
    max_luck_points INTEGER DEFAULT 0,
    spell_slots INTEGER DEFAULT 0,
    spells_used INTEGER DEFAULT 0,
    has_lockpicks BOOLEAN DEFAULT 0,
    cursed BOOLEAN DEFAULT 0,
    poisoned BOOLEAN DEFAULT 0,
    petrified BOOLEAN DEFAULT 0,
    alive BOOLEAN DEFAULT 1,
    position INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS dungeon_runs (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    rooms_explored INTEGER DEFAULT 0,
    monsters_killed INTEGER DEFAULT 0,
    gold_earned INTEGER DEFAULT 0,
    victory BOOLEAN DEFAULT 0,
    final_boss TEXT,
    turns_taken INTEGER DEFAULT 0,
    characters_lost TEXT DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_campaign_chars ON campaign_characters(campaign_id);
CREATE INDEX IF NOT EXISTS idx_dungeon_runs ON dungeon_runs(campaign_id);
"""


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'campaign.db'
)


def _make_connection(db_path: str) -> sqlite3.Connection:
    """Create and configure a SQLite connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if db_path != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db(db_path: str = None, _conn: sqlite3.Connection = None):
    """Context manager for database connections.

    If _conn is provided (for in-memory DBs), reuse it instead of opening
    a new connection. The connection is NOT closed in that case.
    """
    if _conn is not None:
        try:
            yield _conn
            _conn.commit()
        except Exception:
            _conn.rollback()
            raise
        return

    path = db_path or os.environ.get('CAMPAIGN_DB', DEFAULT_DB_PATH)
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = _make_connection(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = None, _conn: sqlite3.Connection = None):
    """Create tables if they don't exist."""
    with get_db(db_path, _conn=_conn) as conn:
        conn.executescript(SCHEMA_SQL)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CampaignSummary:
    id: str
    name: str
    created_at: str
    dungeons_completed: int
    total_gold_earned: int
    characters: List[dict]


# ---------------------------------------------------------------------------
# Character serialization helpers
# ---------------------------------------------------------------------------

def character_to_row(char: Character, campaign_id: str,
                     char_id: str = None) -> dict:
    """Convert a Character object to a dict suitable for DB insertion."""
    d = char.to_dict()
    return {
        'id': char_id or str(uuid.uuid4()),
        'campaign_id': campaign_id,
        'name': d['name'],
        'class_type': d['class_type'],
        'level': d['level'],
        'life': d['life'],
        'max_life': d['max_life'],
        'attack': d['attack'],
        'defense': d['defense'],
        'gold': d.get('gold', 0),
        'equipment': json.dumps(d.get('equipment', [])),
        'inventory_json': json.dumps(
            d.get('inventory') if d.get('inventory') else {}
        ),
        'spells_known': json.dumps(d.get('spells_known', [])),
        'spells_remaining': d.get('spells_remaining', 0),
        'healing_remaining': d.get('healing_remaining', 0),
        'rage_available': d.get('rage_available', True),
        'luck_points': d.get('luck_points', 0),
        'max_luck_points': d.get('max_luck_points', 0),
        'spell_slots': d.get('spell_slots', 0),
        'spells_used': d.get('spells_used', 0),
        'has_lockpicks': d.get('has_lockpicks', False),
        'cursed': d.get('cursed', False),
        'poisoned': d.get('poisoned', False),
        'petrified': d.get('petrified', False),
        'alive': not char.is_dead(),
        'position': d.get('position', 1),
    }


def character_from_row(row: sqlite3.Row) -> Character:
    """Reconstruct a Character object from a DB row."""
    d = dict(row)
    class_type = d['class_type']
    name = d['name']
    level = d.get('level', 1)

    char = create_character(class_type, name, level)

    # Restore core stats
    char.life = d['life']
    char.max_life = d['max_life']
    char.attack = d['attack']
    char.defense = d['defense']
    char.position = d.get('position', 1)

    # Status effects
    char.cursed = bool(d.get('cursed', False))
    char.poisoned = bool(d.get('poisoned', False))
    char.petrified = bool(d.get('petrified', False))

    # Equipment (legacy list)
    char.equipment = json.loads(d.get('equipment', '[]'))

    # Gold -- set via inventory
    gold = d.get('gold', 0)
    if char.inventory:
        char.inventory.gold = gold
    char.gold = gold

    # Spells
    char.spells_known = json.loads(d.get('spells_known', '[]'))
    char.spells_remaining = d.get('spells_remaining', 0)
    char.healing_remaining = d.get('healing_remaining', 0)

    # Class-specific fields
    if isinstance(char, Cleric):
        char.healing_uses = d.get('healing_remaining', 0)
        char.blessing_uses = d.get('spells_remaining', 0)
    elif isinstance(char, Wizard):
        char.spell_slots = d.get('spell_slots', 0)
        char.spells_used = d.get('spells_used', 0)
    elif isinstance(char, Elf):
        char.spell_slots = d.get('spell_slots', 0)
        char.spells_used = d.get('spells_used', 0)
    elif isinstance(char, Barbarian):
        char.rage_available = bool(d.get('rage_available', True))
    elif isinstance(char, Halfling):
        char.luck_points = d.get('luck_points', 0)
        char.max_luck_points = d.get('max_luck_points', 0)
    elif isinstance(char, Rogue):
        char.has_lockpicks = bool(d.get('has_lockpicks', True))

    return char


def heal_between_dungeons(char: Character) -> None:
    """Apply between-dungeon healing per rulebook p.67.

    - Life restored to max
    - Poison and curse cleared
    - Spell slots restored
    - Cleric blessing/healing charges restored
    - Halfling luck points restored
    - Barbarian rage does NOT restore (once per campaign)
    """
    char.life = char.max_life
    char.cursed = False
    char.poisoned = False
    char.limping = False
    char.blessed_temple_bonus = False
    char.separated = False
    char.protected = False

    # Restore spells/abilities
    if isinstance(char, Cleric):
        char.healing_uses = 3
        char.blessing_uses = 3
        char.spells_remaining = 3
        char.healing_remaining = 3
    elif isinstance(char, Wizard):
        char.spell_slots = 2 + char.level
        char.spells_used = 0
        char.spells_remaining = 2 + char.level
    elif isinstance(char, Elf):
        char.spell_slots = char.level
        char.spells_used = 0
        char.spells_remaining = char.level
    elif isinstance(char, Halfling):
        char.luck_points = char.level + 1
        char.max_luck_points = char.level + 1
    # Barbarian rage does NOT reset -- once per campaign


# ---------------------------------------------------------------------------
# Campaign CRUD
# ---------------------------------------------------------------------------

class CampaignManager:
    """Manages campaign persistence via SQLite."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.environ.get(
            'CAMPAIGN_DB', DEFAULT_DB_PATH
        )
        # For :memory: databases, keep a persistent connection so data
        # survives across calls.
        if self.db_path == ":memory:":
            self._conn = _make_connection(":memory:")
        else:
            self._conn = None
        init_db(self.db_path, _conn=self._conn)

    def _get_db(self):
        """Return a context manager for DB access."""
        return get_db(self.db_path, _conn=self._conn)

    def create_campaign(self, name: str,
                        characters: List[Character]) -> str:
        """Create a new campaign with an initial party.

        Returns the campaign ID (UUID).
        """
        campaign_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        with self._get_db() as conn:
            conn.execute(
                """INSERT INTO campaigns (id, name, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (campaign_id, name, now, now),
            )
            for char in characters:
                row = character_to_row(char, campaign_id)
                _insert_character(conn, row)

        return campaign_id

    def save_campaign(self, campaign_id: str,
                      characters: List[Character],
                      run_data: Optional[dict] = None) -> None:
        """Save game state after a dungeon run.

        Applies between-dungeon healing to all living characters, then
        persists them. Optionally records a dungeon run log entry.
        """
        now = datetime.utcnow().isoformat()

        with self._get_db() as conn:
            # Verify campaign exists
            row = conn.execute(
                "SELECT id FROM campaigns WHERE id = ?",
                (campaign_id,),
            ).fetchone()
            if not row:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Delete old characters and re-insert
            conn.execute(
                "DELETE FROM campaign_characters WHERE campaign_id = ?",
                (campaign_id,),
            )

            for char in characters:
                # Apply between-dungeon healing to living characters
                if not char.is_dead() and not char.petrified:
                    heal_between_dungeons(char)

                cdata = character_to_row(char, campaign_id)
                _insert_character(conn, cdata)

            # Record dungeon run if provided
            if run_data:
                run_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO dungeon_runs
                       (id, campaign_id, completed_at, rooms_explored,
                        monsters_killed, gold_earned, victory, final_boss,
                        turns_taken, characters_lost)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id, campaign_id, now,
                        run_data.get('rooms_explored', 0),
                        run_data.get('monsters_killed', 0),
                        run_data.get('gold_earned', 0),
                        run_data.get('victory', False),
                        run_data.get('final_boss', None),
                        run_data.get('turns_taken', 0),
                        json.dumps(run_data.get('characters_lost', [])),
                    ),
                )

                # Update campaign totals
                conn.execute(
                    """UPDATE campaigns SET
                        dungeons_completed = dungeons_completed + 1,
                        total_gold_earned = total_gold_earned + ?,
                        total_monsters_killed = total_monsters_killed + ?,
                        total_rooms_explored = total_rooms_explored + ?,
                        updated_at = ?
                       WHERE id = ?""",
                    (
                        run_data.get('gold_earned', 0),
                        run_data.get('monsters_killed', 0),
                        run_data.get('rooms_explored', 0),
                        now,
                        campaign_id,
                    ),
                )
            else:
                conn.execute(
                    "UPDATE campaigns SET updated_at = ? WHERE id = ?",
                    (now, campaign_id),
                )

    def load_campaign(self, campaign_id: str) -> Optional[dict]:
        """Load campaign state including characters and recent runs.

        Returns None if campaign not found.
        """
        with self._get_db() as conn:
            row = conn.execute(
                "SELECT * FROM campaigns WHERE id = ? AND active = 1",
                (campaign_id,),
            ).fetchone()
            if not row:
                return None

            campaign = dict(row)

            # Load living characters
            char_rows = conn.execute(
                """SELECT * FROM campaign_characters
                   WHERE campaign_id = ? AND alive = 1
                   ORDER BY position""",
                (campaign_id,),
            ).fetchall()
            campaign['characters'] = [
                character_from_row(r) for r in char_rows
            ]

            # Load recent dungeon runs
            runs = conn.execute(
                """SELECT * FROM dungeon_runs
                   WHERE campaign_id = ?
                   ORDER BY completed_at DESC LIMIT 20""",
                (campaign_id,),
            ).fetchall()
            campaign['runs'] = [dict(r) for r in runs]

            return campaign

    def list_campaigns(self) -> List[CampaignSummary]:
        """List all active campaigns."""
        with self._get_db() as conn:
            rows = conn.execute(
                """SELECT * FROM campaigns
                   WHERE active = 1
                   ORDER BY updated_at DESC""",
            ).fetchall()

            result = []
            for row in rows:
                cid = row['id']
                chars = conn.execute(
                    """SELECT name, class_type, level
                       FROM campaign_characters
                       WHERE campaign_id = ? AND alive = 1""",
                    (cid,),
                ).fetchall()
                result.append(CampaignSummary(
                    id=cid,
                    name=row['name'],
                    created_at=row['created_at'],
                    dungeons_completed=row['dungeons_completed'],
                    total_gold_earned=row['total_gold_earned'],
                    characters=[dict(c) for c in chars],
                ))
            return result

    def delete_campaign(self, campaign_id: str) -> bool:
        """Soft-delete a campaign. Returns True if it existed."""
        with self._get_db() as conn:
            cursor = conn.execute(
                "UPDATE campaigns SET active = 0 WHERE id = ? AND active = 1",
                (campaign_id,),
            )
            return cursor.rowcount > 0

    def get_campaign_stats(self, campaign_id: str) -> Optional[dict]:
        """Get campaign statistics."""
        with self._get_db() as conn:
            row = conn.execute(
                "SELECT * FROM campaigns WHERE id = ?",
                (campaign_id,),
            ).fetchone()
            if not row:
                return None

            stats = dict(row)

            # Count characters
            char_count = conn.execute(
                """SELECT
                     COUNT(*) as total,
                     SUM(CASE WHEN alive = 1 THEN 1 ELSE 0 END) as alive
                   FROM campaign_characters
                   WHERE campaign_id = ?""",
                (campaign_id,),
            ).fetchone()
            stats['total_characters'] = char_count['total']
            stats['alive_characters'] = char_count['alive']

            # Count runs
            run_count = conn.execute(
                """SELECT
                     COUNT(*) as total,
                     SUM(CASE WHEN victory = 1 THEN 1 ELSE 0 END) as victories
                   FROM dungeon_runs
                   WHERE campaign_id = ?""",
                (campaign_id,),
            ).fetchone()
            stats['total_runs'] = run_count['total']
            stats['victories'] = run_count['victories']

            return stats


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _insert_character(conn: sqlite3.Connection, row: dict) -> None:
    """Insert a character row into campaign_characters."""
    conn.execute(
        """INSERT INTO campaign_characters
           (id, campaign_id, name, class_type, level, life, max_life,
            attack, defense, gold, equipment, inventory_json,
            spells_known, spells_remaining, healing_remaining,
            rage_available, luck_points, max_luck_points,
            spell_slots, spells_used, has_lockpicks,
            cursed, poisoned, petrified, alive, position)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            row['id'], row['campaign_id'], row['name'], row['class_type'],
            row['level'], row['life'], row['max_life'],
            row['attack'], row['defense'], row['gold'],
            row['equipment'], row['inventory_json'],
            row['spells_known'], row['spells_remaining'],
            row['healing_remaining'],
            row['rage_available'], row['luck_points'],
            row['max_luck_points'], row['spell_slots'],
            row['spells_used'], row['has_lockpicks'],
            row['cursed'], row['poisoned'], row['petrified'],
            row['alive'], row['position'],
        ),
    )
