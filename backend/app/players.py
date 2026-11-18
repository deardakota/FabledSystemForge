"""
Player sheet system for the Story Telling App.

Stores stats, skills, feats, spells, and other character data for players.
Data is stored in memory (MVP) with a persistence layer planned for later.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Character:
    """A player character sheet."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    player_name: str = ""
    level: int = 1
    experience_points: int = 0

    # Core stats
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    # Derived stats
    hit_points: int = 0
    max_hit_points: int = 0
    armor_class: int = 10

    # Skills, feats, spells (created on the fly by the LLM)
    skills: list[str] = field(default_factory=list)
    feats: list[str] = field(default_factory=list)
    spells: list[str] = field(default_factory=list)

    # Inventory and equipment
    inventory: list[str] = field(default_factory=list)
    equipment: dict[str, str] = field(default_factory=dict)

    # Raw stats dict (for on-the-fly stat creation)
    stats: dict[str, int] = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def stat_modifier(self, stat: int) -> int:
        """Return the ability modifier for a given stat score."""
        return (stat - 10) // 2

    def update(self, **updates: Any) -> None:
        """Update fields and refresh the updated_at timestamp."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow().isoformat() + "Z"


class PlayerSheetManager:
    """Manages player character sheets in memory."""

    def __init__(self) -> None:
        self._characters: dict[str, Character] = {}
        self._player_to_characters: dict[str, list[str]] = {}

    def create_character(
        self,
        name: str,
        player_name: str,
        level: int = 1,
        stats: dict[str, int] | None = None,
    ) -> Character:
        """Create a new player character sheet."""
        char_id = str(uuid.uuid4())
        char = Character(
            id=char_id,
            name=name,
            player_name=player_name,
            level=level,
        )
        # Apply starting stats if provided.
        if stats:
            for stat_name in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
                if stat_name in stats:
                    setattr(char, stat_name, stats[stat_name])
            char.stats = dict(stats)
        self._characters[char_id] = char
        self._player_to_characters.setdefault(player_name, []).append(char_id)
        return char

    def get_character(self, char_id: str) -> Character | None:
        """Retrieve a character by ID."""
        return self._characters.get(char_id)

    def get_characters_by_player(self, player_name: str) -> list[Character]:
        """Retrieve all characters for a given player."""
        ids = self._player_to_characters.get(player_name, [])
        return [self._characters[cid] for cid in ids if cid in self._characters]

    def update_character(self, char_id: str, **updates: Any) -> bool:
        """Update a character's fields. Returns True if the character existed."""
        char = self._characters.get(char_id)
        if char is None:
            return False
        char.update(**updates)
        return True

    def delete_character(self, char_id: str) -> bool:
        """Delete a character. Returns True if the character existed."""
        char = self._characters.pop(char_id, None)
        if char is None:
            return False
        # Clean up player index
        for player_name, ids in self._player_to_characters.items():
            if char_id in ids:
                ids.remove(char_id)
                break
        return True

    def list_all(self) -> list[Character]:
        """List all characters."""
        return list(self._characters.values())
