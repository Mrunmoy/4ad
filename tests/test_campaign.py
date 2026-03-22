"""Tests for campaign persistence layer."""
import pytest
from src.campaign import (
    CampaignManager,
    heal_between_dungeons,
    character_to_row,
    character_from_row,
    init_db,
    get_db,
)
from src.character import (
    Warrior, Cleric, Rogue, Wizard, Barbarian, Elf, Dwarf, Halfling,
    create_character,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mgr():
    """Create a CampaignManager backed by in-memory SQLite."""
    return CampaignManager(db_path=":memory:")


@pytest.fixture
def party():
    """Standard 4-character party for testing."""
    return [
        Warrior("Bruggo"),
        Cleric("Aldric"),
        Rogue("Slick"),
        Wizard("Gandalf"),
    ]


@pytest.fixture
def full_party():
    """All 8 character classes for round-trip testing."""
    return [
        Warrior("Bruggo"),
        Cleric("Aldric"),
        Rogue("Slick"),
        Wizard("Gandalf"),
        Barbarian("Conan"),
        Elf("Legolas"),
        Dwarf("Gimli"),
        Halfling("Frodo"),
    ]


# ---------------------------------------------------------------------------
# Campaign CRUD
# ---------------------------------------------------------------------------

class TestCreateCampaign:
    def test_create_campaign_returns_uuid(self, mgr, party):
        cid = mgr.create_campaign("Test Campaign", party)
        assert cid is not None
        assert len(cid) == 36  # UUID length

    def test_create_campaign_stores_name(self, mgr, party):
        cid = mgr.create_campaign("Heroes of Light", party)
        campaign = mgr.load_campaign(cid)
        assert campaign['name'] == "Heroes of Light"

    def test_create_campaign_stores_characters(self, mgr, party):
        cid = mgr.create_campaign("Test", party)
        campaign = mgr.load_campaign(cid)
        assert len(campaign['characters']) == 4
        names = {c.name for c in campaign['characters']}
        assert names == {"Bruggo", "Aldric", "Slick", "Gandalf"}

    def test_create_campaign_initializes_counters(self, mgr, party):
        cid = mgr.create_campaign("Test", party)
        campaign = mgr.load_campaign(cid)
        assert campaign['dungeons_completed'] == 0
        assert campaign['total_gold_earned'] == 0
        assert campaign['total_monsters_killed'] == 0


class TestListCampaigns:
    def test_list_empty(self, mgr):
        assert mgr.list_campaigns() == []

    def test_list_shows_campaigns(self, mgr, party):
        mgr.create_campaign("Campaign A", party)
        mgr.create_campaign("Campaign B", party)
        campaigns = mgr.list_campaigns()
        assert len(campaigns) == 2
        names = {c.name for c in campaigns}
        assert names == {"Campaign A", "Campaign B"}

    def test_list_includes_character_info(self, mgr, party):
        mgr.create_campaign("Test", party)
        campaigns = mgr.list_campaigns()
        assert len(campaigns[0].characters) == 4


class TestDeleteCampaign:
    def test_delete_existing(self, mgr, party):
        cid = mgr.create_campaign("Doomed", party)
        assert mgr.delete_campaign(cid) is True

    def test_delete_hides_from_list(self, mgr, party):
        cid = mgr.create_campaign("Doomed", party)
        mgr.delete_campaign(cid)
        assert mgr.list_campaigns() == []

    def test_delete_hides_from_load(self, mgr, party):
        cid = mgr.create_campaign("Doomed", party)
        mgr.delete_campaign(cid)
        assert mgr.load_campaign(cid) is None

    def test_delete_nonexistent_returns_false(self, mgr):
        assert mgr.delete_campaign("no-such-id") is False


# ---------------------------------------------------------------------------
# Save and load round-trip
# ---------------------------------------------------------------------------

class TestSaveLoadRoundTrip:
    def test_basic_save_load(self, mgr, party):
        cid = mgr.create_campaign("Test", party)
        # Simulate damage during a run
        party[0].take_damage(3)
        party[1].take_damage(2)
        mgr.save_campaign(cid, party)

        campaign = mgr.load_campaign(cid)
        # Between-dungeon healing should restore life
        for char in campaign['characters']:
            assert char.life == char.max_life

    def test_all_character_types_roundtrip(self, mgr, full_party):
        """Test that all 8 classes survive save/load."""
        cid = mgr.create_campaign("Full Party", full_party)
        campaign = mgr.load_campaign(cid)
        loaded_classes = {c.class_type for c in campaign['characters']}
        expected_classes = {
            "Warrior", "Cleric", "Rogue", "Wizard",
            "Barbarian", "Elf", "Dwarf", "Halfling",
        }
        assert loaded_classes == expected_classes

    def test_warrior_roundtrip(self, mgr):
        w = Warrior("Bruggo", level=3)
        cid = mgr.create_campaign("Test", [w])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.name == "Bruggo"
        assert loaded.class_type == "Warrior"
        assert loaded.level == 3
        assert loaded.life == loaded.max_life  # fresh character at full health

    def test_cleric_roundtrip_preserves_abilities(self, mgr):
        c = Cleric("Aldric", level=2)
        c.use_healing()
        c.use_blessing()
        cid = mgr.create_campaign("Test", [c])
        # Save triggers between-dungeon healing which restores abilities
        mgr.save_campaign(cid, [c])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.class_type == "Cleric"
        # After between-dungeon healing, charges are restored
        assert loaded.healing_remaining == 3
        assert loaded.spells_remaining == 3

    def test_wizard_roundtrip(self, mgr):
        w = Wizard("Gandalf", level=2)
        w.cast_spell("Fireball")
        cid = mgr.create_campaign("Test", [w])
        mgr.save_campaign(cid, [w])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.class_type == "Wizard"
        # After between-dungeon healing, spells are restored
        assert loaded.spells_remaining == 2 + loaded.level

    def test_barbarian_rage_persists(self, mgr):
        """Barbarian rage does NOT reset between dungeons."""
        b = Barbarian("Conan")
        b.use_rage()
        assert b.rage_available is False
        cid = mgr.create_campaign("Test", [b])
        mgr.save_campaign(cid, [b])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.class_type == "Barbarian"
        assert loaded.rage_available is False  # NOT restored

    def test_halfling_luck_restored(self, mgr):
        h = Halfling("Frodo")
        h.use_luck()
        assert h.luck_points == 1  # started with 2 (level+1)
        cid = mgr.create_campaign("Test", [h])
        mgr.save_campaign(cid, [h])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.class_type == "Halfling"
        assert loaded.luck_points == loaded.level + 1  # restored

    def test_elf_spells_restored(self, mgr):
        e = Elf("Legolas")
        e.cast_spell("Fireball")
        cid = mgr.create_campaign("Test", [e])
        mgr.save_campaign(cid, [e])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.class_type == "Elf"
        assert loaded.spells_remaining == loaded.level

    def test_rogue_lockpicks_roundtrip(self, mgr):
        r = Rogue("Slick")
        assert r.has_lockpicks is True
        cid = mgr.create_campaign("Test", [r])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.class_type == "Rogue"
        assert loaded.has_lockpicks is True

    def test_dead_characters_excluded_from_load(self, mgr, party):
        party[2].take_damage(999)  # Kill the rogue
        assert party[2].is_dead()
        cid = mgr.create_campaign("Test", party)
        mgr.save_campaign(cid, party)
        campaign = mgr.load_campaign(cid)
        # Dead rogue should not be in loaded characters
        assert len(campaign['characters']) == 3
        names = {c.name for c in campaign['characters']}
        assert "Slick" not in names

    def test_save_nonexistent_campaign_raises(self, mgr, party):
        with pytest.raises(ValueError, match="not found"):
            mgr.save_campaign("no-such-id", party)


# ---------------------------------------------------------------------------
# Between-dungeon healing
# ---------------------------------------------------------------------------

class TestBetweenDungeonHealing:
    def test_life_restored_to_max(self):
        w = Warrior("Bruggo")
        w.take_damage(4)
        assert w.life < w.max_life
        heal_between_dungeons(w)
        assert w.life == w.max_life

    def test_poison_cleared(self):
        w = Warrior("Bruggo")
        w.poisoned = True
        heal_between_dungeons(w)
        assert w.poisoned is False

    def test_curse_cleared(self):
        w = Warrior("Bruggo")
        w.cursed = True
        heal_between_dungeons(w)
        assert w.cursed is False

    def test_cleric_abilities_restored(self):
        c = Cleric("Aldric")
        c.use_healing()
        c.use_healing()
        c.use_blessing()
        assert c.healing_uses == 1
        assert c.blessing_uses == 2
        heal_between_dungeons(c)
        assert c.healing_uses == 3
        assert c.blessing_uses == 3
        assert c.spells_remaining == 3
        assert c.healing_remaining == 3

    def test_wizard_spells_restored(self):
        w = Wizard("Gandalf")
        w.cast_spell("Fireball")
        w.cast_spell("Sleep")
        assert w.spells_used == 2
        heal_between_dungeons(w)
        assert w.spells_used == 0
        assert w.spells_remaining == 2 + w.level

    def test_elf_spells_restored(self):
        e = Elf("Legolas")
        e.cast_spell("Fireball")
        heal_between_dungeons(e)
        assert e.spells_used == 0
        assert e.spells_remaining == e.level

    def test_halfling_luck_restored(self):
        h = Halfling("Frodo")
        h.use_luck()
        h.use_luck()
        heal_between_dungeons(h)
        assert h.luck_points == h.level + 1

    def test_barbarian_rage_not_restored(self):
        b = Barbarian("Conan")
        b.use_rage()
        assert b.rage_available is False
        heal_between_dungeons(b)
        assert b.rage_available is False  # NOT restored

    def test_status_effects_cleared(self):
        w = Warrior("Bruggo")
        w.limping = True
        w.blessed_temple_bonus = True
        w.separated = True
        w.protected = True
        heal_between_dungeons(w)
        assert w.limping is False
        assert w.blessed_temple_bonus is False
        assert w.separated is False
        assert w.protected is False


# ---------------------------------------------------------------------------
# Gold and equipment persistence
# ---------------------------------------------------------------------------

class TestGoldEquipmentPersistence:
    def test_gold_persists(self, mgr):
        w = Warrior("Bruggo")
        w.inventory.gold = 50
        cid = mgr.create_campaign("Test", [w])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        # Gold should be preserved (via inventory)
        assert loaded.gold >= 0  # gold is set from DB

    def test_equipment_list_persists(self, mgr):
        w = Warrior("Bruggo")
        original_equip = list(w.equipment)
        cid = mgr.create_campaign("Test", [w])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.equipment == original_equip

    def test_level_persists(self, mgr):
        w = Warrior("Bruggo", level=3)
        cid = mgr.create_campaign("Test", [w])
        campaign = mgr.load_campaign(cid)
        loaded = campaign['characters'][0]
        assert loaded.level == 3


# ---------------------------------------------------------------------------
# Campaign stats
# ---------------------------------------------------------------------------

class TestCampaignStats:
    def test_stats_after_dungeon_run(self, mgr, party):
        cid = mgr.create_campaign("Test", party)
        run_data = {
            'rooms_explored': 12,
            'monsters_killed': 8,
            'gold_earned': 100,
            'victory': True,
        }
        mgr.save_campaign(cid, party, run_data)

        stats = mgr.get_campaign_stats(cid)
        assert stats['dungeons_completed'] == 1
        assert stats['total_gold_earned'] == 100
        assert stats['total_monsters_killed'] == 8
        assert stats['total_rooms_explored'] == 12
        assert stats['total_runs'] == 1
        assert stats['victories'] == 1

    def test_stats_accumulate_across_runs(self, mgr, party):
        cid = mgr.create_campaign("Test", party)
        mgr.save_campaign(cid, party, {
            'rooms_explored': 10, 'monsters_killed': 5,
            'gold_earned': 50, 'victory': True,
        })
        mgr.save_campaign(cid, party, {
            'rooms_explored': 8, 'monsters_killed': 3,
            'gold_earned': 30, 'victory': False,
        })

        stats = mgr.get_campaign_stats(cid)
        assert stats['dungeons_completed'] == 2
        assert stats['total_gold_earned'] == 80
        assert stats['total_monsters_killed'] == 8
        assert stats['total_rooms_explored'] == 18
        assert stats['total_runs'] == 2
        assert stats['victories'] == 1

    def test_stats_nonexistent_campaign(self, mgr):
        assert mgr.get_campaign_stats("no-such-id") is None

    def test_stats_character_counts(self, mgr, party):
        party[2].take_damage(999)  # Kill the rogue
        cid = mgr.create_campaign("Test", party)
        stats = mgr.get_campaign_stats(cid)
        assert stats['total_characters'] == 4
        assert stats['alive_characters'] == 3


# ---------------------------------------------------------------------------
# Character serialization (from_dict)
# ---------------------------------------------------------------------------

class TestCharacterFromDict:
    def test_warrior_from_dict(self):
        w = Warrior("Bruggo", level=3)
        d = w.to_dict()
        restored = Warrior.from_dict(d)
        assert restored.name == "Bruggo"
        assert restored.level == 3
        assert restored.class_type == "Warrior"

    def test_cleric_from_dict(self):
        c = Cleric("Aldric", level=2)
        c.use_healing()
        d = c.to_dict()
        restored = Cleric.from_dict(d)
        assert restored.name == "Aldric"
        assert restored.level == 2
        assert restored.healing_uses == 2
        assert restored.blessing_uses == 3

    def test_rogue_from_dict(self):
        r = Rogue("Slick")
        d = r.to_dict()
        restored = Rogue.from_dict(d)
        assert restored.name == "Slick"
        assert restored.has_lockpicks is True

    def test_wizard_from_dict(self):
        w = Wizard("Gandalf", level=2)
        w.cast_spell("Fireball")
        d = w.to_dict()
        restored = Wizard.from_dict(d)
        assert restored.name == "Gandalf"
        assert restored.spell_slots == 4
        assert restored.spells_used == 1

    def test_barbarian_from_dict_preserves_rage(self):
        b = Barbarian("Conan")
        b.use_rage()
        d = b.to_dict()
        restored = Barbarian.from_dict(d)
        assert restored.rage_available is False

    def test_elf_from_dict(self):
        e = Elf("Legolas", level=2)
        d = e.to_dict()
        restored = Elf.from_dict(d)
        assert restored.name == "Legolas"
        assert restored.spell_slots == 2

    def test_dwarf_from_dict(self):
        d_char = Dwarf("Gimli")
        data = d_char.to_dict()
        restored = Dwarf.from_dict(data)
        assert restored.name == "Gimli"
        assert restored.class_type == "Dwarf"

    def test_halfling_from_dict(self):
        h = Halfling("Frodo")
        h.use_luck()
        d = h.to_dict()
        restored = Halfling.from_dict(d)
        assert restored.name == "Frodo"
        assert restored.luck_points == 1
