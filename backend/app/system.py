"""
System generator for the Story Telling App.

Instead of a fixed rulebook, each story session generates a
``SystemProfile`` — a bespoke set of skills, spells, feats, and encounter
templates tailored to the current story theme. Everything (combat, puzzles,
traps, skill checks) resolves through the existing polyhedral dice engine,
so the dice remain the only rigid mechanic.

This keeps every session unique: the LLM invents the mechanics, the DM
curates them, and the players experience them on the fly.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from .dice import DiceRoll, roll_dice


@dataclass
class SkillEntry:
    """A single skill within a mechanic profile."""

    name: str
    description: str
    stat: str  # e.g. "dexterity", "intelligence"
    die_size: int = 20
    difficulty_class: int = 10  # default DC for ability checks using this skill


@dataclass
class SpellEntry:
    """A single spell within a mechanic profile."""

    name: str
    description: str
    level: int = 1
    die_size: int = 20  # attack roll or save die
    damage_die: int | None = None  # e.g. 6 for 1d6
    damage_stat: str | None = None  # stat added to damage


@dataclass
class FeatEntry:
    """A single feat within a mechanic profile."""

    name: str
    description: str
    prerequisite: str | None = None


@dataclass
class EncounterTemplate:
    """A template for an encounter / combat scene."""

    name: str
    description: str
    enemy_name: str
    enemy_hp: int
    enemy_ac: int
    enemy_die_size: int = 20
    objective: str | None = None  # e.g. "survive 3 rounds", "reach the door"


@dataclass
class SystemProfile:
    """
    A complete mechanic profile for a story session.

    This is the "system" that the story will use. It is generated on the fly
    by the LLM based on story context and can be revised mid-session.
    """

    name: str
    theme: str  # e.g. "high fantasy heist", "cyberpunk thriller", "gothic horror"
    skills: list[SkillEntry] = field(default_factory=list)
    spells: list[SpellEntry] = field(default_factory=list)
    feats: list[FeatEntry] = field(default_factory=list)
    encounters: list[EncounterTemplate] = field(default_factory=list)
    default_dc: int = 10
    description: str = ""

    def skill_by_name(self, name: str) -> SkillEntry | None:
        for s in self.skills:
            if s.name.lower() == name.lower():
                return s
        return None

    def spell_by_name(self, name: str) -> SpellEntry | None:
        for s in self.spells:
            if s.name.lower() == name.lower():
                return s
        return None

    def feat_by_name(self, name: str) -> FeatEntry | None:
        for f in self.feats:
            if f.name.lower() == name.lower():
                return f
        return None


class SystemGenerator:
    """
    Generates a SystemProfile from story context using the LLM.

    Parameters
    ----------
    llm:
        An LLMSuggester instance.
    """

    def __init__(self, llm) -> None:
        self.llm = llm

    def generate_profile(
        self,
        story_context: str,
        theme: str | None = None,
        player_characters: list[str] | None = None,
        dm_notes: str | None = None,
    ) -> SystemProfile:
        """
        Ask the LLM to generate a complete mechanic profile for the story.

        Returns a SystemProfile with skills, spells, feats, and encounter
        templates. The profile is a starting point; the DM can edit it.
        """
        prompt = self._build_profile_prompt(
            story_context, theme, player_characters, dm_notes
        )
        response = self.llm._query(prompt, temperature=0.7)
        return self._parse_profile(response.suggestion, theme or "fantasy")

    def _build_profile_prompt(
        self,
        story_context: str,
        theme: str | None,
        player_characters: list[str] | None,
        dm_notes: str | None,
    ) -> str:
        theme = theme or "fantasy"
        parts = [
            "You are a creative game-system designer for a fluid, on-the-fly "
            "Dungeon Master story-telling app.",
            "",
            "The app's ONLY rigid mechanic is polyhedral dice (d20, d10, etc.) "
            "for player interactions. Skills, spells, feats, and encounter "
            "templates are created on the fly and resolve through dice rolls.",
            "",
            f"Story context: {story_context}",
            f"Desired theme: {theme}",
        ]
        if player_characters:
            parts += ["", "Player characters:", "\n".join(f"- {c}" for c in player_characters)]
        if dm_notes:
            parts += ["", "DM notes:", dm_notes]
        parts += [
            "",
            "Design a complete mechanic profile (the 'system' for this session):",
            "",
            "1. Name for the system.",
            "2. A one-sentence description of how the system feels.",
            "3. 4–8 skills: name, description, primary stat (e.g. dexterity, "
            "intelligence, wisdom), default die size (usually d20), and a "
            "default difficulty class (DC, usually 10–20).",
            "4. 2–6 spells: name, description, level (1–5), die size for "
            "attacks/saves, optional damage die (e.g. 8 for 1d8), and "
            "optional damage stat.",
            "5. 2–4 feats: name, description, and optional prerequisite.",
            "6. 3–5 encounter templates: name, description, enemy name, enemy "
            "HP, enemy AC, enemy die size, and optional objective.",
            "",
            "Keep the mechanics open-ended and evocative. Do not create a "
            "rigid rulebook — leave room for improvisation. Output ONLY the "
            "profile in a structured format, one section per numbered item.",
        ]
        return "\n".join(parts)

    def _parse_profile(
        self, raw: str, theme: str
    ) -> SystemProfile:
        """
        Parse the LLM's free-text profile into a SystemProfile.

        The LLM may not follow strict formatting, so we extract what we can
        and fill in sensible defaults. This is intentionally defensive.
        """
        profile = SystemProfile(name=theme.capitalize() + " System", theme=theme)

        # Try to pull a name from the first line or a "Name:" section.
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if lines:
            first = lines[0]
            if first.lower().startswith("name:"):
                profile.name = first[len("name:") :].strip()
                lines = lines[1:]

        # Parse skills section
        in_skills = in_spells = in_feats = in_encounters = False
        for line in lines:
            lower = line.lower()
            # Detect section headers
            if lower.startswith("skills") or lower.startswith("1."):
                in_skills = True
                continue
            if lower.startswith("spells") or lower.startswith("2."):
                in_skills = False
                in_spells = True
                continue
            if lower.startswith("feats") or lower.startswith("3."):
                in_spells = False
                in_feats = True
                continue
            if lower.startswith("encounters") or lower.startswith("4."):
                in_feats = False
                in_encounters = True
                continue

            if in_skills and line.startswith(("-", "•", "*")):
                text = line.lstrip("-•* ").strip()
                skill = self._parse_skill(text, profile.default_dc)
                if skill:
                    profile.skills.append(skill)
            elif in_spells and line.startswith(("-", "•", "*")):
                text = line.lstrip("-•* ").strip()
                spell = self._parse_spell(text)
                if spell:
                    profile.spells.append(spell)
            elif in_feats and line.startswith(("-", "•", "*")):
                text = line.lstrip("-•* ").strip()
                feat = self._parse_feat(text)
                if feat:
                    profile.feats.append(feat)
            elif in_encounters and line.startswith(("-", "•", "*")):
                text = line.lstrip("-•* ").strip()
                enc = self._parse_encounter(text)
                if enc:
                    profile.encounters.append(enc)

        # Ensure at least one skill and one encounter exist so the system is usable.
        if not profile.skills:
            profile.skills.append(
                SkillEntry(
                    name="Knowledge",
                    description="General knowledge and lore checks.",
                    stat="intelligence",
                )
            )
        if not profile.encounters:
            profile.encounters.append(
                EncounterTemplate(
                    name="Random Encounter",
                    description="A generic encounter.",
                    enemy_name="Adversary",
                    enemy_hp=20,
                    enemy_ac=12,
                )
            )

        return profile

    def _parse_skill(self, text: str, default_dc: int) -> SkillEntry | None:
        # Very light parsing: take the name before the first colon or dash.
        name = text.split(":", 1)[0].strip().strip(" -•*")
        if not name:
            return None
        desc = text
        stat = "intelligence"
        for candidate in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
            if candidate in text.lower():
                stat = candidate
                break
        return SkillEntry(name=name, description=desc, stat=stat, die_size=20, difficulty_class=default_dc)

    def _parse_spell(self, text: str) -> SpellEntry | None:
        name = text.split(":", 1)[0].strip().strip(" -•*")
        if not name:
            return None
        return SpellEntry(name=name, description=text, level=1, die_size=20)

    def _parse_feat(self, text: str) -> FeatEntry | None:
        name = text.split(":", 1)[0].strip().strip(" -•*")
        if not name:
            return None
        return FeatEntry(name=name, description=text)

    def _parse_encounter(self, text: str) -> EncounterTemplate | None:
        name = text.split(":", 1)[0].strip().strip(" -•*")
        if not name:
            return None
        return EncounterTemplate(
            name=name,
            description=text,
            enemy_name="Foe",
            enemy_hp=20,
            enemy_ac=12,
        )

    # ------------------------------------------------------------------
    # Resolution helpers that funnel everything through the dice engine.
    # ------------------------------------------------------------------

    def resolve_skill_check(
        self,
        profile: SystemProfile,
        skill_name: str,
        stat_score: int,
        dc: int | None = None,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """
        Resolve a skill check: roll d20 + stat modifier vs DC.

        Returns a dict with the roll, modifier, total, and whether it passed.
        """
        skill = profile.skill_by_name(skill_name)
        if skill is None:
            # Fall back to a generic check using the skill's stat.
            skill = SkillEntry(name=skill_name, description="", stat="intelligence", die_size=20, difficulty_class=dc or profile.default_dc)

        stat_mod = (stat_score - 10) // 2
        target_dc = dc if dc is not None else (skill.difficulty_class or profile.default_dc)
        roll = roll_dice(skill.die_size, seed=seed)
        total = roll.total + stat_mod
        passed = total >= target_dc

        return {
            "skill": skill.name,
            "stat": skill.stat,
            "stat_score": stat_score,
            "modifier": stat_mod,
            "roll": roll.total,
            "total": total,
            "dc": target_dc,
            "passed": passed,
            "individual": list(roll.results),
        }

    def resolve_spell_attack(
        self,
        profile: SystemProfile,
        spell_name: str,
        attack_stat_score: int,
        target_ac: int,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """
        Resolve a spell attack: roll d20 + stat modifier vs AC.
        """
        spell = profile.spell_by_name(spell_name)
        if spell is None:
            spell = SpellEntry(name=spell_name, description="", die_size=20)

        stat_mod = (attack_stat_score - 10) // 2
        roll = roll_dice(spell.die_size, seed=seed)
        total = roll.total + stat_mod
        hit = total >= target_ac

        damage = 0
        damage_details: list[str] = []
        if hit and spell.damage_die:
            dmg_roll = roll_dice(spell.damage_die, seed=seed)
            damage = dmg_roll.total
            damage_details.append(f"{spell.damage_die}d{spell.damage_die} = {damage}")
            if spell.damage_stat:
                dmg_mod = (attack_stat_score - 10) // 2
                damage += dmg_mod
                damage_details.append(f"+ {dmg_mod} ({spell.damage_stat})")

        return {
            "spell": spell.name,
            "roll": roll.total,
            "modifier": stat_mod,
            "total": total,
            "ac": target_ac,
            "hit": hit,
            "damage": damage,
            "damage_details": damage_details,
            "individual": list(roll.results),
        }

    def resolve_encounter(
        self,
        profile: SystemProfile,
        encounter_name: str,
        player_actions: list[str],
        seed: int | None = None,
    ) -> dict[str, Any]:
        """
        Resolve an encounter using the LLM for narration and dice for the
        outcome. The encounter template provides the enemy stats.
        """
        enc = next((e for e in profile.encounters if e.name.lower() == encounter_name.lower()), None)
        if enc is None:
            enc = EncounterTemplate(
                name=encounter_name,
                description="Generic encounter.",
                enemy_name="Foe",
                enemy_hp=20,
                enemy_ac=12,
            )

        # Roll for the enemy's defense (AC check).
        enemy_roll = roll_dice(enc.enemy_die_size, seed=seed)
        enemy_total = enemy_roll.total + ((enc.enemy_hp - 10) // 4)  # rough stat
        # Player rolls against the enemy.
        player_roll = roll_dice(20, seed=seed)
        player_total = player_roll.total

        # Use the LLM to narrate.
        prompt = (
            f"Narrate an encounter. Enemy: {enc.enemy_name} (HP {enc.enemy_hp}, AC {enc.enemy_ac}). "
            f"Player roll: {player_total}. Enemy roll: {enemy_total}. "
            f"Player actions: {'; '.join(player_actions) if player_actions else 'none'}. "
            f"Encounter description: {enc.description}. "
            f"Narrate the outcome based on the rolls. Keep it vivid and concise."
        )
        narrative = self.llm._query(prompt, temperature=0.6)

        return {
            "encounter": enc.name,
            "enemy": enc.enemy_name,
            "enemy_hp": enc.enemy_hp,
            "enemy_ac": enc.enemy_ac,
            "player_roll": player_total,
            "enemy_roll": enemy_total,
            "player_success": player_total > enemy_total,
            "narrative": narrative.suggestion if narrative else "",
        }
