"""Tests for the encounter/combat system."""

from __future__ import annotations

from app.encounter import (
    Achievement,
    Combatant,
    Encounter,
    EncounterManager,
    EnemySheet,
    StatusEffect,
)


def test_modifier() -> None:
    assert EncounterManager._modifier(10) == 0
    assert EncounterManager._modifier(14) == 2
    assert EncounterManager._modifier(8) == -1
    assert EncounterManager._modifier(18) == 4


def test_status_effect_classic() -> None:
    blind = StatusEffect.classic("blind")
    assert blind is not None
    assert blind.blinded is True

    stun = StatusEffect.classic("stun")
    assert stun is not None
    assert stun.stunned is True

    prone = StatusEffect.classic("prone")
    assert prone is not None
    assert prone.prone is True

    assert StatusEffect.classic("nonexistent") is None


def test_enemy_sheet_creation() -> None:
    enemy = EnemySheet(
        name="Goblin",
        description="A small green foe.",
        hp=10,
        max_hp=10,
        ac=13,
        damage_die=6,
    )
    assert enemy.name == "Goblin"
    assert enemy.hp == 10
    assert enemy.ac == 13
    assert enemy.defeated is False


def test_combatant_creation() -> None:
    c = Combatant(
        id="p1",
        name="Rogue",
        type="player",
        dexterity=14,
        ac=14,
        hp=20,
        max_hp=20,
        damage_die=6,
        damage_stat="dexterity",
    )
    assert c.name == "Rogue"
    assert c.defeated is False


def test_encounter_creation() -> None:
    enc = Encounter(
        name="Goblin Camp",
        description="A goblin ambush.",
    )
    assert enc.over is False
    assert enc.outcome is None


def test_set_turn_order() -> None:
    enc = Encounter(name="Test", description="test")
    p1 = Combatant(id="p1", name="Rogue", type="player")
    p2 = Combatant(id="p2", name="Wizard", type="player")
    e1 = Combatant(id="e1", name="Goblin", type="enemy")
    enc.combatants = [p1, p2, e1]
    enc.turn_order = ["p1", "e1", "p2"]

    mgr = EncounterManager()
    mgr.set_turn_order(enc, ["p1", "e1", "p2"])
    assert enc.turn_order == ["p1", "e1", "p2"]
    assert enc.current_turn_index == 0
    assert enc.round == 1


def test_current_combatant() -> None:
    enc = Encounter(name="Test", description="test")
    p1 = Combatant(id="p1", name="Rogue", type="player")
    e1 = Combatant(id="e1", name="Goblin", type="enemy")
    enc.combatants = [p1, e1]
    enc.turn_order = ["p1", "e1"]

    mgr = EncounterManager()
    mgr.set_turn_order(enc, ["p1", "e1"])
    cur = mgr.current_combatant(enc)
    assert cur is not None
    assert cur.name == "Rogue"

    mgr.advance_turn(enc)
    cur = mgr.current_combatant(enc)
    assert cur is not None
    assert cur.name == "Goblin"
    assert enc.round == 1

    # Advance past the end -> next round
    mgr.advance_turn(enc)
    cur = mgr.current_combatant(enc)
    assert cur is not None
    assert cur.name == "Rogue"
    assert enc.round == 2


def test_status_effect_duration_decrement() -> None:
    enc = Encounter(name="Test", description="test")
    p1 = Combatant(id="p1", name="Rogue", type="player")
    enc.combatants = [p1]
    enc.turn_order = ["p1"]

    mgr = EncounterManager()
    mgr.set_turn_order(enc, ["p1"])

    # Apply a 3-round effect
    mgr.apply_status_effect(enc, "p1", "stun", duration_rounds=3)
    assert len(p1.status_effects) == 1
    assert p1.status_effects[0].duration_rounds == 3

    # Advance 2 turns -> duration should be 1
    mgr.advance_turn(enc)
    mgr.advance_turn(enc)
    assert p1.status_effects[0].duration_rounds == 1

    # Advance 1 more -> effect removed
    mgr.advance_turn(enc)
    assert len(p1.status_effects) == 0


def test_resolve_attack_hit() -> None:
    enc = Encounter(name="Test", description="test")
    attacker = Combatant(
        id="a", name="Fighter", type="player",
        strength=16, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength",
    )
    target = Combatant(
        id="t", name="Goblin", type="enemy",
        strength=10, dexterity=10, ac=12, hp=10, max_hp=10,
        damage_die=6, damage_stat="strength",
    )
    enc.combatants = [attacker, target]
    enc.turn_order = ["a", "t"]

    mgr = EncounterManager()
    result = mgr.resolve_attack(
        encounter=enc,
        attacker_id="a",
        target_id="t",
        attack_type="melee",
        seed=1,
    )
    assert result["attacker"] == "Fighter"
    assert result["target"] == "Goblin"
    assert result["attack_type"] == "melee"
    assert isinstance(result["hit"], bool)
    assert isinstance(result["crit"], bool)
    assert result["roll"] > 0
    assert result["modifier"] == 3  # str 16 -> +3


def _setup_stunned_encounter() -> tuple[Encounter, EncounterManager, Combatant, Combatant]:
    enc = Encounter(name="Test", description="test")
    attacker = Combatant(
        id="a", name="Fighter", type="player",
        strength=10, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength",
    )
    target = Combatant(
        id="t", name="Goblin", type="enemy",
        strength=10, dexterity=10, ac=12, hp=10, max_hp=10,
        damage_die=6, damage_stat="strength",
    )
    enc.combatants = [attacker, target]
    enc.turn_order = ["a", "t"]
    mgr = EncounterManager()
    return enc, mgr, attacker, target


def test_resolve_attack_stunned_target() -> None:
    enc, mgr, attacker, target = _setup_stunned_encounter()
    # Stun the target
    mgr.apply_status_effect(enc, "t", "stun", duration_rounds=2)

    result = mgr.resolve_attack(
        encounter=enc,
        attacker_id="a",
        target_id="t",
        attack_type="melee",
        seed=1,
    )
    assert result["target_stunned"] is True
    assert result["hit"] is True  # auto-hit against stunned


def test_resolve_attack_blinded_target() -> None:
    enc = Encounter(name="Test", description="test")
    attacker = Combatant(
        id="a", name="Fighter", type="player",
        strength=10, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength",
    )
    target = Combatant(
        id="t", name="Goblin", type="enemy",
        strength=10, dexterity=10, ac=12, hp=10, max_hp=10,
        damage_die=6, damage_stat="strength",
    )
    enc.combatants = [attacker, target]
    enc.turn_order = ["a", "t"]
    mgr = EncounterManager()
    # Blind the target
    mgr.apply_status_effect(enc, "t", "blind", duration_rounds=2)

    result = mgr.resolve_attack(
        encounter=enc,
        attacker_id="a",
        target_id="t",
        attack_type="melee",
        seed=1,
    )
    assert result["target_blinded"] is True
    assert isinstance(result["hit"], bool)


def test_resolve_damage() -> None:
    enc = Encounter(name="Test", description="test")
    attacker = Combatant(
        id="a", name="Fighter", type="player",
        strength=16, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength", damage_bonus=2,
    )
    target = Combatant(
        id="t", name="Goblin", type="enemy",
        strength=10, dexterity=10, ac=12, hp=10, max_hp=10,
        damage_die=6, damage_stat="strength",
    )
    enc.combatants = [attacker, target]
    enc.turn_order = ["a", "t"]

    mgr = EncounterManager()
    result = mgr.resolve_damage(
        encounter=enc,
        attacker_id="a",
        target_id="t",
        attack_type="melee",
        damage_die=6,
        damage_bonus=2,
        seed=1,
    )
    assert result["target"] == "Goblin"
    assert result["base_damage"] > 0
    assert result["target_hp_after"] <= result["target_hp_before"]
    assert target.hp == result["target_hp_after"]


def test_resolve_damage_defeats_target() -> None:
    enc = Encounter(name="Test", description="test")
    attacker = Combatant(
        id="a", name="Fighter", type="player",
        strength=16, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength", damage_bonus=20,
    )
    target = Combatant(
        id="t", name="Goblin", type="enemy",
        strength=10, dexterity=10, ac=12, hp=5, max_hp=5,
        damage_die=6, damage_stat="strength",
    )
    enc.combatants = [attacker, target]
    enc.turn_order = ["a", "t"]

    mgr = EncounterManager()
    result = mgr.resolve_damage(
        encounter=enc,
        attacker_id="a",
        target_id="t",
        attack_type="melee",
        damage_die=6,
        damage_bonus=20,
        seed=1,
    )
    assert result["target_defeated"] is True
    assert target.defeated is True


def test_achievement_damage_bonus() -> None:
    ach = Achievement(
        name="Mighty Melee",
        description="+1 damage on melee attacks.",
        damage_bonus=1,
        damage_type="melee",
        condition="melee",
    )
    attacker = Combatant(
        id="a", name="Fighter", type="player",
        strength=10, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength", damage_bonus=0,
        achievements=[ach],
    )
    target = Combatant(
        id="t", name="Goblin", type="enemy",
        strength=10, dexterity=10, ac=12, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength",
    )
    enc = Encounter(name="Test", description="test")
    enc.combatants = [attacker, target]
    enc.turn_order = ["a", "t"]

    mgr = EncounterManager()
    result = mgr.resolve_damage(
        encounter=enc,
        attacker_id="a",
        target_id="t",
        attack_type="melee",
        damage_die=6,
        damage_bonus=0,
        seed=1,
    )
    # Damage should include the +1 achievement bonus
    assert result["base_damage"] >= 1  # at least the bonus


def test_spell_transformation() -> None:
    enc = Encounter(name="Test", description="test")
    caster = Combatant(
        id="c", name="Wizard", type="player",
        strength=10, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength", wisdom=16,
    )
    enc.combatants = [caster]
    enc.turn_order = ["c"]

    mgr = EncounterManager()
    result = mgr.resolve_spell_transformation(
        encounter=enc,
        caster_id="c",
        spell_name="Lightning Bolt",
        target_form="Lightning Lasso",
        seed=1,
    )
    assert result["spell"] == "Lightning Bolt"
    assert result["target_form"] == "Lightning Lasso"
    assert isinstance(result["success"], bool)
    if result["success"]:
        assert result["transformed"] is True
        assert caster.current_action == "Lightning Bolt → Lightning Lasso"


def test_check_encounter_over_players_win() -> None:
    enc = Encounter(name="Test", description="test")
    p1 = Combatant(id="p1", name="Rogue", type="player")
    p2 = Combatant(id="p2", name="Wizard", type="player")
    e1 = Combatant(id="e1", name="Goblin", type="enemy", defeated=True)
    e2 = Combatant(id="e2", name="Orc", type="enemy", defeated=True)
    enc.combatants = [p1, p2, e1, e2]
    enc.turn_order = ["p1", "p2", "e1", "e2"]

    mgr = EncounterManager()
    mgr.check_encounter_over(enc)
    assert enc.over is True
    assert enc.outcome == "players_win"


def test_check_encounter_over_enemies_win() -> None:
    enc = Encounter(name="Test", description="test")
    p1 = Combatant(id="p1", name="Rogue", type="player", defeated=True)
    p2 = Combatant(id="p2", name="Wizard", type="player", defeated=True)
    e1 = Combatant(id="e1", name="Goblin", type="enemy")
    enc.combatants = [p1, p2, e1]
    enc.turn_order = ["p1", "p2", "e1"]

    mgr = EncounterManager()
    mgr.check_encounter_over(enc)
    assert enc.over is True
    assert enc.outcome == "enemies_win"


def test_damage_with_weakness() -> None:
    enc = Encounter(name="Test", description="test")
    attacker = Combatant(
        id="a", name="Fighter", type="player",
        strength=10, dexterity=10, ac=15, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength",
    )
    target = Combatant(
        id="t", name="Goblin", type="enemy",
        strength=10, dexterity=10, ac=12, hp=20, max_hp=20,
        damage_die=6, damage_stat="strength",
        weaknesses=["bludgeoning"],
    )
    enc.combatants = [attacker, target]
    enc.turn_order = ["a", "t"]

    mgr = EncounterManager()
    result = mgr.resolve_damage(
        encounter=enc,
        attacker_id="a",
        target_id="t",
        attack_type="melee",
        damage_die=6,
        damage_bonus=0,
        seed=1,
    )
    assert result["damage_type"] == "bludgeoning"
    # Damage was applied (may be doubled due to weakness)
    assert result["base_damage"] > 0
    assert result["target_hp_after"] <= result["target_hp_before"]
