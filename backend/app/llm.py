"""
LLM integration module for the Story Telling App.

Provides on-the-fly story suggestions, combat outcome generation,
and NPC/monster descriptions driven by microphone listening input.

Uses Ollama as the default local LLM provider, with a cloud/Hermes
fallback for tasks that benefit from it.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any

from .dice import DiceRoll, roll_dice, roll_with_advantage, roll_with_disadvantage


@dataclass
class LLMResponse:
    """Structured response from the LLM."""

    suggestion: str
    confidence: float
    dice_roll: DiceRoll | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMSuggester:
    """
    Generates on-the-fly story suggestions using a local LLM (Ollama).

    Parameters
    ----------
    model:
        Ollama model name to use (default: qwen3.5:latest).
    base_url:
        Ollama API base URL (default: http://127.0.0.1:11434).
    """

    def __init__(self, model: str = "qwen3.5:latest", base_url: str = "http://127.0.0.1:11434") -> None:
        self.model = model
        self.base_url = base_url
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check whether Ollama is reachable."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and self.model in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_available(self) -> bool:
        """Return True if the configured LLM model is available."""
        return self._available

    def suggest_story_arc(
        self,
        current_context: str,
        player_characters: list[str],
        dm_notes: str | None = None,
    ) -> LLMResponse:
        """
        Ask the LLM for story arc suggestions, villains, surprises,
        clues, and riddles based on the current context.
        """
        prompt = self._build_story_prompt(current_context, player_characters, dm_notes)
        return self._query(prompt, temperature=0.7)

    def suggest_combat_outcome(
        self,
        encounter_description: str,
        player_actions: list[str],
        dice_roll: DiceRoll,
        enemy_description: str | None = None,
    ) -> LLMResponse:
        """
        Ask the LLM to describe a combat outcome based on player actions
        and dice rolls. The dice roll is the source of truth for success
        or failure; the LLM narrates the result.
        """
        prompt = self._build_combat_prompt(
            encounter_description, player_actions, dice_roll, enemy_description
        )
        return self._query(prompt, temperature=0.6)

    def suggest_npc(
        self,
        name: str,
        role: str,
        context: str,
    ) -> LLMResponse:
        """Ask the LLM to generate an NPC/monster description and stats."""
        prompt = (
            f"Create an NPC/monster for a story. "
            f"Name: {name}\n"
            f"Role: {role}\n"
            f"Context: {context}\n\n"
            f"Provide: a description, role in the story, "
            f"key abilities, and suggested stats. Keep it concise."
        )
        return self._query(prompt, temperature=0.7)

    def _build_story_prompt(
        self,
        current_context: str,
        player_characters: list[str],
        dm_notes: str | None,
    ) -> str:
        parts = [
            "You are a creative Dungeon Master assistant. "
            "The players want a fluid, on-the-fly story with minimal rigid structure. "
            "The only rigid mechanic is polyhedral dice (d20, d10, etc.) for player interactions. "
            "Spells, skills, feats, story arcs, villains, surprises, clues, riddles, "
            "and combat outcomes are created on the fly.",
            "",
            "Current story context:",
            current_context,
            "",
            "Player characters involved:",
            "\n".join(f"- {c}" for c in player_characters),
        ]
        if dm_notes:
            parts += ["", "DM notes:", dm_notes]
        parts += [
            "",
            "Suggest:",
            "1. A story arc or plot development for what happens next.",
            "2. A villain or antagonist with motivations.",
            "3. A surprise or twist.",
            "4. A clue or riddle for the players to solve.",
            "5. Any relevant NPCs or monsters.",
            "",
            "Keep the suggestions open-ended so the players can improvise. "
            "Do not prescribe rigid mechanics—leave outcomes to dice rolls.",
        ]
        return "\n".join(parts)

    def _build_combat_prompt(
        self,
        encounter_description: str,
        player_actions: list[str],
        dice_roll: DiceRoll,
        enemy_description: str | None,
    ) -> str:
        parts = [
            "You are a creative Dungeon Master assistant narrating combat. "
            "The dice roll is the source of truth for success or failure. "
            "Narrate the result accordingly.",
            "",
            "Encounter:",
            encounter_description,
            "",
            "Enemy:",
            enemy_description or "Unknown foe",
            "",
            "Player actions:",
            "\n".join(f"- {a}" for a in player_actions),
            "",
            f"Dice roll result: {dice_roll.total} (individual rolls: {dice_roll.individual})",
            "",
            "Narrate the combat outcome based on the dice roll. "
            "Describe what happens, whether the players succeed or fail, "
            "and any consequences. Keep it vivid and concise.",
        ]
        return "\n".join(parts)

    def _query(self, prompt: str, temperature: float = 0.7) -> LLMResponse:
        """Send a prompt to the LLM and parse the response."""
        if not self._available:
            return LLMResponse(
                suggestion=(
                    "LLM not available. Ollama model "
                    f"{self.model} is not running or not pulled. "
                    "Start Ollama and pull the model, or configure a cloud provider."
                ),
                confidence=0.0,
            )

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-X",
                    "POST",
                    f"{self.base_url}/api/generate",
                    "-H",
                    "Content-Type: application/json",
                    "-d",
                    json.dumps(
                        {
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": temperature},
                        }
                    ),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                return LLMResponse(
                    suggestion=f"LLM request failed: {result.stderr}",
                    confidence=0.0,
                )

            data = json.loads(result.stdout)
            suggestion = data.get("response", "No response from LLM.")
            confidence = 0.8 if suggestion else 0.0

            # Optionally extract a suggested dice roll if the LLM mentions one.
            dice_roll = None
            return LLMResponse(
                suggestion=suggestion,
                confidence=confidence,
                dice_roll=dice_roll,
            )

        except (json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            return LLMResponse(
                suggestion=f"LLM request error: {exc}",
                confidence=0.0,
            )
