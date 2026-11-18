"""Tests for the system generator module."""

from __future__ import annotations

from app.llm import LLMResponse
from app.system import (
    EncounterTemplate,
    FeatEntry,
    SkillEntry,
    SpellEntry,
    SystemGenerator,
    SystemProfile,
)


class FakeLLM:
    """Minimal LLM substitute for tests."""

    def __init__(self) -> None:
        self.available = True

    def _query(self, prompt: str, temperature: float = 0.7) -> LLMResponse:
        from app.llm import LLMResponse

        return LLMResponse(
            suggestion=(
                "Name: Test System\n"
                "Description: A test system.\n"
                "Skills:\n"
                "- Stealth: sneak around. Stat: dexterity. DC: 12.\n"
                "- Knowledge: know things. Stat: intelligence. DC: 10.\n"
                "Spells:\n"
                "- Light: a light spell. Level 1.\n"
                "Feats:\n"
                "- Tough: extra hp.\n"
                "Encounters:\n"
                "- Goblin Camp: fight goblins. Enemy: Goblin. HP 10. AC 13.\n"
            ),
            confidence=0.8,
        )

    def is_available(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# SystemProfile tests
# ---------------------------------------------------------------------------

def test_profile_creation() -> None:
    profile = SystemProfile(name="Test System", theme="fantasy")
    assert profile.name == "Test System"
    assert profile.theme == "fantasy"
    assert profile.default_dc == 10


def test_profile_skill_by_name() -> None:
    profile = SystemProfile(
        name="Test", theme="fantasy",
        skills=[SkillEntry(name="Stealth", description="sneak", stat="dexterity")],
    )
    found = profile.skill_by_name("Stealth")
    assert found is not None
    assert found.name == "Stealth"
    assert profile.skill_by_name("nonexistent") is None


def test_profile_spell_by_name() -> None:
    profile = SystemProfile(
        name="Test", theme="fantasy",
        spells=[SpellEntry(name="Fireball", description="boom", level=3)],
    )
    found = profile.spell_by_name("Fireball")
    assert found is not None
    assert found.level == 3


def test_profile_feat_by_name() -> None:
    profile = SystemProfile(
        name="Test", theme="fantasy",
        feats=[FeatEntry(name="Tough", description="hp+")],
    )
    found = profile.feat_by_name("Tough")
    assert found is not None


def test_profile_encounters() -> None:
    profile = SystemProfile(
        name="Test", theme="fantasy",
        encounters=[EncounterTemplate(name="Goblin Camp", description="goblins", enemy_name="Goblin", enemy_hp=10, enemy_ac=13)],
    )
    assert len(profile.encounters) == 1
    assert profile.encounters[0].enemy_name == "Goblin"


# ---------------------------------------------------------------------------
# SystemGenerator tests
# ---------------------------------------------------------------------------

def test_generate_profile_returns_profile() -> None:
    gen = SystemGenerator(FakeLLM())
    profile = gen.generate_profile(
        story_context="A heist in a noble manor.",
        theme="fantasy heist",
        player_characters=["Rogue", "Wizard"],
        dm_notes="Keep it sneaky.",
    )
    assert profile.name == "Test System"
    assert profile.theme == "fantasy heist"
    assert len(profile.skills) >= 1
    assert len(profile.encounters) >= 1


def test_resolve_skill_check() -> None:
    profile = SystemProfile(
        name="Test", theme="fantasy",
        skills=[SkillEntry(name="Stealth", description="sneak", stat="dexterity", difficulty_class=12)],
    )
    gen = SystemGenerator(FakeLLM())
    result = gen.resolve_skill_check(
        profile=profile,
        skill_name="Stealth",
        stat_score=14,  # modifier +2
        dc=12,
        seed=42,
    )
    assert result["skill"] == "Stealth"
    assert result["modifier"] == 2
    assert result["dc"] == 12
    assert isinstance(result["passed"], bool)


def test_resolve_spell_attack() -> None:
    profile = SystemProfile(
        name="Test", theme="fantasy",
        spells=[SpellEntry(name="Fireball", description="boom", die_size=20, damage_die=6, damage_stat="intelligence")],
    )
    gen = SystemGenerator(FakeLLM())
    result = gen.resolve_spell_attack(
        profile=profile,
        spell_name="Fireball",
        attack_stat_score=16,  # modifier +3
        target_ac=14,
        seed=42,
    )
    assert result["spell"] == "Fireball"
    assert result["modifier"] == 3
    assert isinstance(result["hit"], bool)


def test_resolve_encounter() -> None:
    profile = SystemProfile(
        name="Test", theme="fantasy",
        encounters=[EncounterTemplate(name="Goblin Camp", description="goblins", enemy_name="Goblin", enemy_hp=10, enemy_ac=13)],
    )
    gen = SystemGenerator(FakeLLM())
    result = gen.resolve_encounter(
        profile=profile,
        encounter_name="Goblin Camp",
        player_actions=["sneak up", "distract"],
        seed=42,
    )
    assert result["encounter"] == "Goblin Camp"
    assert result["enemy"] == "Goblin"
    assert isinstance(result["player_success"], bool)
    assert isinstance(result["narrative"], str)
