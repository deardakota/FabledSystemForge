"""
Encounter / combat system for the Story Telling App.

Provides per-turn phased combat resolution:

1. Attack order phase — DM sets turn order for players and enemies.
2. Hit-or-miss phase — d20 + stat vs AC.
3. Status-effect phase — apply effects (blind, stun, prone, custom).
4. Damage phase — polyhedral damage rolls (d4, d6, d8, d10, d12, d20).

Enemy sheets store per-enemy stats, weaknesses, resistances, spells, and skills
so the DM can tailor encounters on the fly. Achievements (milestones) can
modify damage, movement, or other numbers. A spell can be transformed on a
successful roll (e.g. Lightning Bolt → Lightning Lasso) and the LLM
narrates the outcome.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from .dice import (
    DiceRoll,
    roll_dice,
    roll_with_advantage,
    roll_with_disadvantage,
)


# ---------------------------------------------------------------------------
# Status effects
# ---------------------------------------------------------------------------

@dataclass
class StatusEffect:
    """A status effect applied to a combatant."""

    name: str
    description: str
    duration_rounds: int = 2  # how many rounds it persists
    stacks: bool = False
    # Effect modifiers (applied to the target's stats/rolls)
    ac_penalty: int = 0
    attack_penalty: int = 0
    save_penalty: int = 0
    movement_penalty: int = 0
    # Flags
    stunned: bool = False
    prone: bool = False
    blinded: bool = False

    @classmethod
    def classic(cls, name: str) -> "StatusEffect" | None:
        return _CLASSIC_EFFECTS.get(name)


# Module-level classic effects (defined after the class).
_CLASSIC_EFFECTS: dict[str, StatusEffect] = {
    "blind": StatusEffect(
        name="Blinded",
        description="Attack rolls against the blinded target have disadvantage.",
        ac_penalty=0,
        attack_penalty=0,  # disadvantage handled in combat logic
        duration_rounds=2,
        blinded=True,
    ),
    "stun": StatusEffect(
        name="Stunned",
        description="The target cannot take actions or reactions.",
        duration_rounds=1,
        stunned=True,
    ),
    "prone": StatusEffect(
        name="Prone",
        description="Melee attacks against the prone target have advantage; "
        "the target spends half movement to stand up.",
        movement_penalty=2,
        prone=True,
    ),
    "poison": StatusEffect(
        name="Poisoned",
        description="The target takes 1d4 poison damage at the start of each turn.",
        duration_rounds=3,
    ),
    "fear": StatusEffect(
        name="Frightened",
        description="The target has disadvantage on ability checks and attacks "
        "while the source of fear is within sight.",
        attack_penalty=0,
        duration_rounds=2,
    ),
    "silenced": StatusEffect(
        name="Silenced",
        description="The target cannot cast spells with verbal components.",
        duration_rounds=2,
    ),
}


# ---------------------------------------------------------------------------
# Achievements
# ---------------------------------------------------------------------------

@dataclass
class Achievement:
    """A milestone achievement that provides a passive or conditional bonus."""

    name: str
    description: str
    # What it modifies
    damage_bonus: int = 0
    damage_type: str | None = None  # e.g. "melee", "ranged", "spell"
    attack_bonus: int = 0
    ac_bonus: int = 0
    movement_bonus: int = 0
    # Condition: when does it apply?
    condition: str | None = None  # e.g. "melee", "spell", "lightning", "crit"


# ---------------------------------------------------------------------------
# Enemy sheet
# ---------------------------------------------------------------------------

@dataclass
class EnemySheet:
    """A per-enemy stat block the DM can tailor on the fly."""

    name: str
    description: str
    hp: int
    max_hp: int
    ac: int
    # Ability scores
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    # Damage die for melee
    damage_die: int = 6  # e.g. 6 for 1d6
    damage_stat: str = "strength"
    damage_bonus: int = 0
    # Weaknesses / resistances (list of damage types or conditions)
    weaknesses: list[str] = field(default_factory=list)
    resistances: list[str] = field(default_factory=list)
    immunities: list[str] = field(default_factory=list)
    # Spells and skills the enemy can use
    spells: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    # Status effects currently on the enemy
    status_effects: list[StatusEffect] = field(default_factory=list)
    # Achievements the enemy has (rare, for special enemies)
    achievements: list[Achievement] = field(default_factory=list)
    # Whether the enemy is defeated
    defeated: bool = False


# ---------------------------------------------------------------------------
# Combatant (player or enemy)
# ---------------------------------------------------------------------------

@dataclass
class Combatant:
    """A participant in an encounter — either a player character or an enemy."""

    id: str
    name: str
    type: str  # "player" or "enemy"
    # Stats
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    ac: int = 10
    hp: int = 10
    max_hp: int = 10
    # Damage die for melee attacks
    damage_die: int = 6
    damage_stat: str = "strength"
    damage_bonus: int = 0
    # Weaknesses / resistances
    weaknesses: list[str] = field(default_factory=list)
    resistances: list[str] = field(default_factory=list)
    immunities: list[str] = field(default_factory=list)
    # Status effects
    status_effects: list[StatusEffect] = field(default_factory=list)
    # Achievements
    achievements: list[Achievement] = field(default_factory=list)
    # Current spell / action being used (for transformation)
    current_action: str | None = None
    # Whether defeated
    defeated: bool = False


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------

@dataclass
class Encounter:
    """A complete encounter with players and enemies, turn order, and state."""

    name: str
    description: str
    combatants: list[Combatant] = field(default_factory=list)
    # Turn order: list of combatant IDs in order
    turn_order: list[str] = field(default_factory=list)
    current_turn_index: int = 0
    round: int = 1
    # Whether the encounter is over
    over: bool = False
    # Outcome
    outcome: str | None = None  # "players_win", "enemies_win", "escape"


# ---------------------------------------------------------------------------
# EncounterManager
# ---------------------------------------------------------------------------

class EncounterManager:
    """
    Manages an encounter: turn order, phased resolution, damage, status effects,
    achievements, and spell transformation.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _modifier(score: int) -> int:
        return (score - 10) // 2

    @staticmethod
    def _get_combatant(encounter: Encounter, cid: str) -> Combatant | None:
        for c in encounter.combatants:
            if c.id == cid:
                return c
        return None

    @staticmethod
    def _apply_effect_modifiers(
        combatant: Combatant,
    ) -> dict[str, int]:
        """Return penalty/bonus modifiers from active status effects."""
        ac_penalty = 0
        attack_penalty = 0
        movement_penalty = 0
        stunned = False
        prone = False
        blinded = False
        for eff in combatant.status_effects:
            ac_penalty += eff.ac_penalty
            attack_penalty += eff.attack_penalty
            movement_penalty += eff.movement_penalty
            if eff.stunned:
                stunned = True
            if eff.prone:
                prone = True
            if eff.blinded:
                blinded = True
        return {
            "ac_penalty": ac_penalty,
            "attack_penalty": attack_penalty,
            "movement_penalty": movement_penalty,
            "stunned": stunned,
            "prone": prone,
            "blinded": blinded,
        }

    # ------------------------------------------------------------------
    # Turn order
    # ------------------------------------------------------------------

    def set_turn_order(
        self,
        encounter: Encounter,
        order: list[str],
    ) -> None:
        """Set the attack order (list of combatant IDs)."""
        encounter.turn_order = order
        encounter.current_turn_index = 0
        encounter.round = 1

    def current_combatant(self, encounter: Encounter) -> Combatant | None:
        if not encounter.turn_order:
            return None
        cid = encounter.turn_order[encounter.current_turn_index]
        return self._get_combatant(encounter, cid)

    def advance_turn(self, encounter: Encounter) -> None:
        """Advance to the next combatant in turn order."""
        if not encounter.turn_order:
            return
        encounter.current_turn_index += 1
        if encounter.current_turn_index >= len(encounter.turn_order):
            encounter.current_turn_index = 0
            encounter.round += 1
        # Decrement status effect durations
        for c in encounter.combatants:
            for eff in c.status_effects[:]:
                eff.duration_rounds -= 1
                if eff.duration_rounds <= 0:
                    c.status_effects.remove(eff)

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def roll_damage(
        self,
        damage_die: int,
        damage_bonus: int,
        seed: int | None = None,
        extra_dice: int = 0,
        extra_die_size: int = 0,
    ) -> DiceRoll:
        """Roll damage: ``damage_die`` + bonus, plus optional extra dice."""
        dice = [damage_die] * (1 + extra_dice)
        sizes = [damage_die] * (1 + extra_dice)
        if extra_die_size:
            sizes[-1] = extra_die_size
        roll = roll_dice(*tuple(sizes), seed=seed)
        # Add bonus to the total for display; base damage is roll.total + bonus
        return roll

    # ------------------------------------------------------------------
    # Hit or miss
    # ------------------------------------------------------------------

    def resolve_attack(
        self,
        encounter: Encounter,
        attacker_id: str,
        target_id: str,
        attack_type: str = "melee",  # melee, ranged, spell
        dice_size: int = 20,
        seed: int | None = None,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> dict[str, Any]:
        """
        Phase 2: Hit or miss.

        Returns a dict with the roll, total, hit/miss, and modifiers.
        """
        attacker = self._get_combatant(encounter, attacker_id)
        target = self._get_combatant(encounter, target_id)
        if attacker is None or target is None:
            raise ValueError("Combatant not found")

        # Status effect modifiers from target (defensive)
        target_mods = self._apply_effect_modifiers(target)
        # Status effect modifiers from attacker (offensive)
        attacker_mods = self._apply_effect_modifiers(attacker)

        # Determine stat for attack
        if attack_type == "spell":
            attack_stat = attacker.wisdom  # default; can be overridden
        else:
            attack_stat = attacker.dexterity if attack_type == "ranged" else attacker.strength

        attack_modifier = self._modifier(attack_stat)

        # Achievement bonuses
        for ach in attacker.achievements:
            if ach.condition in (None, attack_type):
                attack_modifier += ach.attack_bonus

        # Prone advantage: melee attacks against prone targets have advantage
        if attack_type == "melee" and target_mods["prone"]:
            advantage = True

        # Blinded: attacks against blinded targets have disadvantage
        if target_mods["blinded"] and attack_type != "spell":
            disadvantage = True

        # Stunned targets cannot defend
        roll: DiceRoll | None = None
        total = 0
        effective_ac = target.ac + target_mods["ac_penalty"]
        if target_mods["stunned"]:
            # Auto-hit
            hit = True
            crit = True
            # Still roll for display purposes
            roll = roll_dice(dice_size, seed=seed)
            total = roll.total + attack_modifier
        else:
            # Roll d20
            if advantage:
                roll = roll_with_advantage((dice_size,), seed=seed)
            elif disadvantage:
                roll = roll_with_disadvantage((dice_size,), seed=seed)
            else:
                roll = roll_dice(dice_size, seed=seed)

            total = roll.total + attack_modifier
            # AC with penalty
            hit = total >= effective_ac
            # Critical on natural 20
            crit = roll.total == dice_size

        return {
            "attacker": attacker.name,
            "target": target.name,
            "attack_type": attack_type,
            "roll": roll.total,
            "modifier": attack_modifier,
            "total": total,
            "ac": effective_ac,
            "hit": hit,
            "crit": crit,
            "target_stunned": target_mods["stunned"],
            "target_prone": target_mods["prone"],
            "target_blinded": target_mods["blinded"],
        }

    # ------------------------------------------------------------------
    # Spell transformation
    # ------------------------------------------------------------------

    def resolve_spell_transformation(
        self,
        encounter: Encounter,
        caster_id: str,
        spell_name: str,
        target_form: str,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """
        Phase: attempt to transform a spell on a successful roll.

        The caster rolls a d20 + Wisdom modifier vs a DC (default 15).
        On success, the spell transforms into the target form for the rest
        of the encounter.
        """
        caster = self._get_combatant(encounter, caster_id)
        if caster is None:
            raise ValueError("Caster not found")

        modifier = self._modifier(caster.wisdom)
        roll = roll_dice(20, seed=seed)
        total = roll.total + modifier
        dc = 15
        success = total >= dc

        transformed = False
        if success:
            # Record the transformation on the caster
            caster.current_action = f"{spell_name} → {target_form}"
            transformed = True

        return {
            "spell": spell_name,
            "target_form": target_form,
            "roll": roll.total,
            "modifier": modifier,
            "total": total,
            "dc": dc,
            "success": success,
            "transformed": transformed,
        }

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def resolve_damage(
        self,
        encounter: Encounter,
        attacker_id: str,
        target_id: str,
        attack_type: str = "melee",
        damage_die: int = 6,
        damage_bonus: int = 0,
        seed: int | None = None,
        extra_dice: int = 0,
        extra_die_size: int = 0,
        critical: bool = False,
    ) -> dict[str, Any]:
        """
        Phase 4: Damage.

        Rolls damage dice, applies bonuses, weaknesses/resistances, and
        achievements. Returns damage dealt and target's new HP.
        """
        attacker = self._get_combatant(encounter, attacker_id)
        target = self._get_combatant(encounter, target_id)
        if attacker is None or target is None:
            raise ValueError("Combatant not found")

        # Roll damage
        roll = self.roll_damage(
            damage_die, damage_bonus, seed=seed,
            extra_dice=extra_dice, extra_die_size=extra_die_size,
        )
        base_damage = roll.total + damage_bonus

        # Achievement damage bonus
        for ach in attacker.achievements:
            if ach.condition in (None, attack_type):
                base_damage += ach.damage_bonus

        # Critical hits: double the damage dice (add one more damage die)
        if critical:
            extra_roll = self.roll_damage(damage_die, 0, seed=seed)
            base_damage += extra_roll.total

        # Apply target weaknesses/resistances
        # Determine damage type (default: attacker's damage stat)
        damage_type = attacker.damage_stat
        if damage_type == "strength":
            damage_type = "bludgeoning"
        elif damage_type == "dexterity":
            damage_type = "piercing"

        # Simple weakness/resistance logic
        if damage_type in target.weaknesses:
            base_damage *= 2
        if damage_type in target.resistances:
            base_damage //= 2

        # Apply damage
        target.hp = max(0, target.hp - base_damage)
        if target.hp <= 0:
            target.defeated = True

        return {
            "attacker": attacker.name,
            "target": target.name,
            "base_damage": base_damage,
            "damage_type": damage_type,
            "target_hp_before": target.hp + base_damage,
            "target_hp_after": target.hp,
            "target_defeated": target.defeated,
            "individual": roll.individual,
            "dice_sizes": [damage_die] * (1 + extra_dice),
        }

    # ------------------------------------------------------------------
    # Status effects
    # ------------------------------------------------------------------

    def apply_status_effect(
        self,
        encounter: Encounter,
        target_id: str,
        effect_name: str,
        duration_rounds: int = 2,
        custom_description: str | None = None,
    ) -> dict[str, Any]:
        """Apply a status effect to a target."""
        target = self._get_combatant(encounter, target_id)
        if target is None:
            raise ValueError("Target not found")

        effect = StatusEffect.classic(effect_name)
        if effect is None:
            # Custom effect
            effect = StatusEffect(
                name=effect_name,
                description=custom_description or effect_name,
                duration_rounds=duration_rounds,
            )
        else:
            effect.duration_rounds = duration_rounds
            if custom_description:
                effect.description = custom_description

        target.status_effects.append(effect)

        return {
            "target": target.name,
            "effect": effect.name,
            "description": effect.description,
            "duration_rounds": effect.duration_rounds,
            "stunned": effect.stunned,
            "prone": effect.prone,
            "blinded": effect.blinded,
        }

    # ------------------------------------------------------------------
    # Enemy sheet from LLM
    # ------------------------------------------------------------------

    def create_enemy_from_description(
        self,
        name: str,
        description: str,
        hp: int | None = None,
        ac: int | None = None,
        damage_die: int | None = None,
    ) -> EnemySheet:
        """Create an enemy sheet from a DM description (LLM would fill this)."""
        return EnemySheet(
            name=name,
            description=description,
            hp=hp or 20,
            max_hp=hp or 20,
            ac=ac or 12,
            damage_die=damage_die or 6,
        )

    # ------------------------------------------------------------------
    # Check if encounter is over
    # ------------------------------------------------------------------

    def check_encounter_over(self, encounter: Encounter) -> None:
        """Determine if the encounter is over and set the outcome."""
        players_defeated = all(c.defeated for c in encounter.combatants if c.type == "player")
        enemies_defeated = all(c.defeated for c in encounter.combatants if c.type == "enemy")

        if players_defeated and encounter.combatants:
            encounter.over = True
            encounter.outcome = "enemies_win"
        elif enemies_defeated and encounter.combatants:
            encounter.over = True
            encounter.outcome = "players_win"
        elif not encounter.combatants:
            encounter.over = True
            encounter.outcome = "draw"
