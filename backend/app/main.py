"""
FastAPI backend for the Story Telling App.

Endpoints:
- POST /dice/roll — roll polyhedral dice (d20, d10, etc.)
- POST /dice/compare — compare a roll to a target number
- GET /players — list all player characters
- POST /players — create a player character
- GET /players/{id} — get a character
- PUT /players/{id} — update a character
- DELETE /players/{id} — delete a character
- POST /llm/suggest-story — LLM story arc suggestions
- POST /llm/suggest-combat — LLM combat outcome narration
- POST /llm/suggest-npc — LLM NPC/monster generation
- GET /health — health check
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .dice import (
    DiceError,
    compare_to_target,
    roll_dice,
    roll_d20,
    roll_d10,
    roll_percentile,
    roll_with_advantage,
    roll_with_disadvantage,
)
from .encounter import (
    Achievement,
    Combatant,
    Encounter,
    EncounterManager,
    EnemySheet,
    StatusEffect,
)
from .llm import LLMSuggester, LLMResponse
from .players import Character, PlayerSheetManager
from .system import (
    EncounterTemplate,
    FeatEntry,
    SkillEntry,
    SpellEntry,
    SystemProfile,
    SystemGenerator,
)

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Story Telling App — DM Companion",
    description="A fluid Dungeon Master story-teller companion app with "
    "on-the-fly LLM suggestions, dice rolling, player sheets, a "
    "session-generated mechanic system, and phased combat. The only rigid "
    "mechanic is polyhedral dice for player interactions.",
    version="0.1.0",
)

# In-memory managers (MVP — persistence layer planned for later).
player_manager = PlayerSheetManager()
llm_suggester = LLMSuggester()
system_generator = SystemGenerator(llm_suggester)
encounter_manager = EncounterManager()
encounters: dict[str, Encounter] = {}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class DiceRollRequest(BaseModel):
    """Request to roll one or more dice."""

    dice_sizes: list[int] = Field(
        default=[20],
        description="List of die sizes to roll (e.g. [20, 10, 10] for d20+2d10).",
        min_items=1,
    )
    seed: int | None = Field(
        default=None,
        description="Optional seed for reproducible rolls.",
    )
    advantage: bool = Field(default=False, description="Roll with advantage (take higher).")
    disadvantage: bool = Field(default=False, description="Roll with disadvantage (take lower).")


class DiceRollResponse(BaseModel):
    """Response for a dice roll."""

    total: int
    individual: list[int]
    dice_sizes: list[int]
    seed: int | None = None


class CompareRollRequest(BaseModel):
    """Request to compare a roll to a target number."""

    total: int = Field(ge=1, description="The dice roll total.")
    target: int = Field(ge=1, description="The target number to meet or exceed.")


class CompareRollResponse(BaseModel):
    """Response for a dice roll comparison."""

    result: str  # "success", "failure", or "critical"


class CharacterCreateRequest(BaseModel):
    """Request to create a player character."""

    name: str = Field(min_length=1, description="Character name.")
    player_name: str = Field(min_length=1, description="Player's name.")
    level: int = Field(default=1, ge=1, description="Character level.")
    stats: dict[str, int] | None = Field(
        default=None,
        description="Optional starting ability scores (str, dex, con, int, wis, cha).",
    )


class CharacterUpdateRequest(BaseModel):
    """Request to update a player character."""

    name: str | None = None
    player_name: str | None = None
    level: int | None = Field(default=None, ge=1)
    experience_points: int | None = Field(default=None, ge=0)
    strength: int | None = Field(default=None, ge=1, le=20)
    dexterity: int | None = Field(default=None, ge=1, le=20)
    constitution: int | None = Field(default=None, ge=1, le=20)
    intelligence: int | None = Field(default=None, ge=1, le=20)
    wisdom: int | None = Field(default=None, ge=1, le=20)
    charisma: int | None = Field(default=None, ge=1, le=20)
    hit_points: int | None = Field(default=None, ge=0)
    max_hit_points: int | None = Field(default=None, ge=0)
    armor_class: int | None = Field(default=None, ge=0)
    skills: list[str] | None = None
    feats: list[str] | None = None
    spells: list[str] | None = None
    inventory: list[str] | None = None
    equipment: dict[str, str] | None = None


class CharacterResponse(BaseModel):
    """Response for a character."""

    id: str
    name: str
    player_name: str
    level: int
    experience_points: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    hit_points: int
    max_hit_points: int
    armor_class: int
    skills: list[str]
    feats: list[str]
    spells: list[str]
    inventory: list[str]
    equipment: dict[str, str]
    created_at: str
    updated_at: str


class StorySuggestRequest(BaseModel):
    """Request for LLM story suggestions."""

    current_context: str = Field(min_length=1, description="Current story context.")
    player_characters: list[str] = Field(default_factory=list, description="Character names involved.")
    dm_notes: str | None = Field(default=None, description="DM notes for the LLM.")


class StorySuggestResponse(BaseModel):
    """Response for a story suggestion."""

    suggestion: str
    confidence: float
    dice_roll: DiceRollResponse | None = None


class CombatSuggestRequest(BaseModel):
    """Request for LLM combat outcome narration."""

    encounter_description: str = Field(min_length=1)
    player_actions: list[str] = Field(default_factory=list)
    dice_sizes: list[int] = Field(default=[20], min_items=1)
    seed: int | None = None
    advantage: bool = Field(default=False)
    disadvantage: bool = Field(default=False)
    enemy_description: str | None = None


class CombatSuggestResponse(BaseModel):
    """Response for a combat suggestion."""

    suggestion: str
    confidence: float
    dice_roll: DiceRollResponse | None = None


class NPCSuggestRequest(BaseModel):
    """Request for LLM NPC generation."""

    name: str = Field(min_length=1)
    role: str = Field(min_length=1, description="NPC role (e.g. villain, ally, merchant).")
    context: str = Field(min_length=1, description="Story context for the NPC.")


class NPCSuggestResponse(BaseModel):
    """Response for an NPC suggestion."""

    suggestion: str
    confidence: float


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "story-telling-app"}


@app.get("/llm/status")
async def llm_status() -> dict[str, Any]:
    """Check whether the LLM provider is available."""
    return {
        "available": llm_suggester.is_available(),
        "model": llm_suggester.model,
        "base_url": llm_suggester.base_url,
    }


# ---------------------------------------------------------------------------
# Dice endpoints
# ---------------------------------------------------------------------------

@app.post("/dice/roll", response_model=DiceRollResponse)
async def roll_dice_endpoint(request: DiceRollRequest) -> DiceRollResponse:
    """Roll one or more polyhedral dice."""
    try:
        if request.advantage and request.disadvantage:
            raise HTTPException(
                status_code=400,
                detail="Cannot specify both advantage and disadvantage.",
            )

        if request.advantage:
            result = roll_with_advantage(tuple(request.dice_sizes), seed=request.seed)
        elif request.disadvantage:
            result = roll_with_disadvantage(tuple(request.dice_sizes), seed=request.seed)
        else:
            result = roll_dice(*request.dice_sizes, seed=request.seed)

        return DiceRollResponse(
            total=result.total,
            individual=list(result.results),
            dice_sizes=list(request.dice_sizes),
            seed=request.seed,
        )
    except DiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/dice/compare", response_model=CompareRollResponse)
async def compare_roll_endpoint(request: CompareRollRequest) -> CompareRollResponse:
    """Compare a dice roll total to a target number."""
    result = compare_to_target(request.total, request.target)
    return CompareRollResponse(result=result)


# ---------------------------------------------------------------------------
# Player sheet endpoints
# ---------------------------------------------------------------------------

@app.get("/players", response_model=list[CharacterResponse])
async def list_players() -> list[CharacterResponse]:
    """List all player characters."""
    return [_character_to_response(c) for c in player_manager.list_all()]


@app.post("/players", response_model=CharacterResponse, status_code=201)
async def create_player(request: CharacterCreateRequest) -> CharacterResponse:
    """Create a new player character."""
    char = player_manager.create_character(
        name=request.name,
        player_name=request.player_name,
        level=request.level,
        stats=request.stats,
    )
    return _character_to_response(char)


@app.get("/players/{char_id}", response_model=CharacterResponse)
async def get_player(char_id: str) -> CharacterResponse:
    """Get a player character by ID."""
    char = player_manager.get_character(char_id)
    if char is None:
        raise HTTPException(status_code=404, detail="Character not found.")
    return _character_to_response(char)


@app.put("/players/{char_id}", response_model=CharacterResponse)
async def update_player(char_id: str, request: CharacterUpdateRequest) -> CharacterResponse:
    """Update a player character."""
    updates = {
        k: v
        for k, v in request.model_dump(exclude_unset=True).items()
        if v is not None
    }
    if not updates:
        # No changes — return the existing character.
        char = player_manager.get_character(char_id)
        if char is None:
            raise HTTPException(status_code=404, detail="Character not found.")
        return _character_to_response(char)

    success = player_manager.update_character(char_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found.")
    char = player_manager.get_character(char_id)
    assert char is not None
    return _character_to_response(char)


@app.delete("/players/{char_id}")
async def delete_player(char_id: str) -> dict[str, str]:
    """Delete a player character."""
    success = player_manager.delete_character(char_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found.")
    return {"status": "deleted", "id": char_id}


# ---------------------------------------------------------------------------
# LLM suggestion endpoints
# ---------------------------------------------------------------------------

@app.post("/llm/suggest-story", response_model=StorySuggestResponse)
async def suggest_story(request: StorySuggestRequest) -> StorySuggestResponse:
    """Get LLM story arc suggestions."""
    response = llm_suggester.suggest_story_arc(
        current_context=request.current_context,
        player_characters=request.player_characters,
        dm_notes=request.dm_notes,
    )
    return StorySuggestResponse(
        suggestion=response.suggestion,
        confidence=response.confidence,
        dice_roll=(
            DiceRollResponse(
                total=response.dice_roll.total,
                individual=list(response.dice_roll.results),
                dice_sizes=[d.sides for d in response.dice_roll.dice],
                seed=None,
            )
            if response.dice_roll
            else None
        ),
    )


@app.post("/llm/suggest-combat", response_model=CombatSuggestResponse)
async def suggest_combat(request: CombatSuggestRequest) -> CombatSuggestResponse:
    """Get LLM combat outcome narration."""
    # Roll the dice first (source of truth).
    try:
        if request.advantage and request.disadvantage:
            raise HTTPException(
                status_code=400,
                detail="Cannot specify both advantage and disadvantage.",
            )
        if request.advantage:
            dice_result = roll_with_advantage(tuple(request.dice_sizes), seed=request.seed)
        elif request.disadvantage:
            dice_result = roll_with_disadvantage(tuple(request.dice_sizes), seed=request.seed)
        else:
            dice_result = roll_dice(*request.dice_sizes, seed=request.seed)
    except DiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Ask the LLM to narrate the outcome.
    response = llm_suggester.suggest_combat_outcome(
        encounter_description=request.encounter_description,
        player_actions=request.player_actions,
        dice_roll=dice_result,
        enemy_description=request.enemy_description,
    )

    return CombatSuggestResponse(
        suggestion=response.suggestion,
        confidence=response.confidence,
        dice_roll=DiceRollResponse(
            total=dice_result.total,
            individual=list(dice_result.results),
            dice_sizes=list(request.dice_sizes),
            seed=request.seed,
        ),
    )


@app.post("/llm/suggest-npc", response_model=NPCSuggestResponse)
async def suggest_npc(request: NPCSuggestRequest) -> NPCSuggestResponse:
    """Get LLM NPC/monster generation."""
    response = llm_suggester.suggest_npc(
        name=request.name,
        role=request.role,
        context=request.context,
    )
    return NPCSuggestResponse(
        suggestion=response.suggestion,
        confidence=response.confidence,
    )


# ---------------------------------------------------------------------------
# System generator endpoints
# ---------------------------------------------------------------------------

class SystemGenerateRequest(BaseModel):
    """Request to generate a session mechanic profile."""

    story_context: str = Field(min_length=1, description="Current story context.")
    theme: str | None = Field(
        default=None,
        description="Desired theme (e.g. fantasy heist, cyberpunk, gothic horror).",
    )
    player_characters: list[str] = Field(
        default_factory=list,
        description="Character names involved.",
    )
    dm_notes: str | None = Field(default=None, description="DM notes for the LLM.")


class SystemGenerateResponse(BaseModel):
    """Response for a generated system profile."""

    name: str
    theme: str
    description: str
    skills: list[SkillEntry]
    spells: list[SpellEntry]
    feats: list[FeatEntry]
    encounters: list[EncounterTemplate]
    default_dc: int


class SkillCheckRequest(BaseModel):
    """Request to resolve a skill check."""

    skill_name: str
    stat_score: int = Field(ge=1, le=20, description="Ability score (1–20).")
    dc: int | None = Field(default=None, ge=1, description="Target DC (uses profile default if omitted).")
    seed: int | None = Field(default=None, description="Optional seed for reproducible rolls.")


class SkillCheckResponse(BaseModel):
    """Response for a skill check."""

    skill: str
    stat: str
    stat_score: int
    modifier: int
    roll: int
    total: int
    dc: int
    passed: bool
    individual: list[int]


class SpellAttackRequest(BaseModel):
    """Request to resolve a spell attack."""

    spell_name: str
    attack_stat_score: int = Field(ge=1, le=20, description="Ability score (1–20).")
    target_ac: int = Field(ge=1, description="Target AC.")
    seed: int | None = Field(default=None, description="Optional seed for reproducible rolls.")


class SpellAttackResponse(BaseModel):
    """Response for a spell attack."""

    spell: str
    roll: int
    modifier: int
    total: int
    ac: int
    hit: bool
    damage: int
    damage_details: list[str]
    individual: list[int]


class EncounterResolveRequest(BaseModel):
    """Request to resolve an encounter."""

    encounter_name: str
    player_actions: list[str] = Field(default_factory=list)
    seed: int | None = Field(default=None, description="Optional seed for reproducible rolls.")


class EncounterResolveResponse(BaseModel):
    """Response for an encounter resolution."""

    encounter: str
    enemy: str
    enemy_hp: int
    enemy_ac: int
    player_roll: int
    enemy_roll: int
    player_success: bool
    narrative: str


@app.post("/system/generate", response_model=SystemGenerateResponse)
async def generate_system(request: SystemGenerateRequest) -> SystemGenerateResponse:
    """Generate a session mechanic profile (skills, spells, feats, encounters)."""
    profile = system_generator.generate_profile(
        story_context=request.story_context,
        theme=request.theme,
        player_characters=request.player_characters,
        dm_notes=request.dm_notes,
    )
    return SystemGenerateResponse(
        name=profile.name,
        theme=profile.theme,
        description=profile.description,
        skills=profile.skills,
        spells=profile.spells,
        feats=profile.feats,
        encounters=profile.encounters,
        default_dc=profile.default_dc,
    )


@app.post("/system/skill-check", response_model=SkillCheckResponse)
async def skill_check(request: SkillCheckRequest) -> SkillCheckResponse:
    """Resolve a skill check: d20 + stat modifier vs DC."""
    # We need a profile to resolve against. Use a default profile if none is
    # stored on the request context. For MVP, generate a generic profile.
    profile = SystemProfile(name="Default", theme="generic")
    result = system_generator.resolve_skill_check(
        profile=profile,
        skill_name=request.skill_name,
        stat_score=request.stat_score,
        dc=request.dc,
        seed=request.seed,
    )
    return SkillCheckResponse(
        skill=result["skill"],
        stat=result["stat"],
        stat_score=result["stat_score"],
        modifier=result["modifier"],
        roll=result["roll"],
        total=result["total"],
        dc=result["dc"],
        passed=result["passed"],
        individual=result["individual"],
    )


@app.post("/system/spell-attack", response_model=SpellAttackResponse)
async def spell_attack(request: SpellAttackRequest) -> SpellAttackResponse:
    """Resolve a spell attack: d20 + stat modifier vs AC."""
    profile = SystemProfile(name="Default", theme="generic")
    result = system_generator.resolve_spell_attack(
        profile=profile,
        spell_name=request.spell_name,
        attack_stat_score=request.attack_stat_score,
        target_ac=request.target_ac,
        seed=request.seed,
    )
    return SpellAttackResponse(
        spell=result["spell"],
        roll=result["roll"],
        modifier=result["modifier"],
        total=result["total"],
        ac=result["ac"],
        hit=result["hit"],
        damage=result["damage"],
        damage_details=result["damage_details"],
        individual=result["individual"],
    )


@app.post("/system/encounter", response_model=EncounterResolveResponse)
async def resolve_encounter(request: EncounterResolveRequest) -> EncounterResolveResponse:
    """Resolve an encounter using dice + LLM narration."""
    profile = SystemProfile(name="Default", theme="generic")
    result = system_generator.resolve_encounter(
        profile=profile,
        encounter_name=request.encounter_name,
        player_actions=request.player_actions,
        seed=request.seed,
    )
    return EncounterResolveResponse(
        encounter=result["encounter"],
        enemy=result["enemy"],
        enemy_hp=result["enemy_hp"],
        enemy_ac=result["enemy_ac"],
        player_roll=result["player_roll"],
        enemy_roll=result["enemy_roll"],
        player_success=result["player_success"],
        narrative=result["narrative"],
    )


# ---------------------------------------------------------------------------
# Encounter API models
# ---------------------------------------------------------------------------

class StatusEffectRequest(BaseModel):
    """Request to apply a status effect."""

    target_id: str
    effect_name: str
    duration_rounds: int = Field(default=2, ge=1)
    custom_description: str | None = None


class StatusEffectResponse(BaseModel):
    """Response for a status effect."""

    target: str
    effect: str
    description: str
    duration_rounds: int
    stunned: bool
    prone: bool
    blinded: bool


class CombatantRequest(BaseModel):
    """Request to create a combatant."""

    id: str
    name: str
    type: str = Field(default="player", description="player or enemy")
    strength: int = Field(default=10, ge=1, le=20)
    dexterity: int = Field(default=10, ge=1, le=20)
    constitution: int = Field(default=10, ge=1, le=20)
    intelligence: int = Field(default=10, ge=1, le=20)
    wisdom: int = Field(default=10, ge=1, le=20)
    charisma: int = Field(default=10, ge=1, le=20)
    ac: int = Field(default=10, ge=0)
    hp: int = Field(default=10, ge=0)
    max_hp: int = Field(default=10, ge=0)
    damage_die: int = Field(default=6, description="Damage die size (4, 6, 8, 10, 12, 20).")
    damage_stat: str = Field(default="strength")
    damage_bonus: int = Field(default=0, ge=0)
    weaknesses: list[str] = Field(default_factory=list)
    resistances: list[str] = Field(default_factory=list)
    immunities: list[str] = Field(default_factory=list)


class CombatantResponse(BaseModel):
    """Response for a combatant."""

    id: str
    name: str
    type: str
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    ac: int
    hp: int
    max_hp: int
    damage_die: int
    damage_stat: str
    damage_bonus: int
    weaknesses: list[str]
    resistances: list[str]
    immunities: list[str]
    status_effects: list[dict]
    achievements: list[dict]
    current_action: str | None
    defeated: bool


class EncounterCreateRequest(BaseModel):
    """Request to create an encounter."""

    name: str
    description: str
    combatants: list[CombatantRequest]


class EncounterResponse(BaseModel):
    """Response for an encounter."""

    name: str
    description: str
    combatants: list[CombatantResponse]
    turn_order: list[str]
    current_turn_index: int
    round: int
    over: bool
    outcome: str | None


class SetTurnOrderRequest(BaseModel):
    """Request to set attack order."""

    encounter_id: str
    order: list[str]


class AttackRequest(BaseModel):
    """Request to resolve an attack (hit or miss)."""

    encounter_id: str
    attacker_id: str
    target_id: str
    attack_type: str = Field(default="melee", description="melee, ranged, or spell")
    dice_size: int = Field(default=20, ge=1)
    seed: int | None = None
    advantage: bool = Field(default=False)
    disadvantage: bool = Field(default=False)


class AttackResponse(BaseModel):
    """Response for an attack roll."""

    attacker: str
    target: str
    attack_type: str
    roll: int
    modifier: int
    total: int
    ac: int
    hit: bool
    crit: bool
    target_stunned: bool
    target_prone: bool
    target_blinded: bool


class DamageRequest(BaseModel):
    """Request to resolve damage."""

    encounter_id: str
    attacker_id: str
    target_id: str
    attack_type: str = Field(default="melee")
    damage_die: int = Field(default=6, ge=1)
    damage_bonus: int = Field(default=0, ge=0)
    seed: int | None = None
    extra_dice: int = Field(default=0, ge=0)
    extra_die_size: int = Field(default=0, ge=1)
    critical: bool = Field(default=False)


class DamageResponse(BaseModel):
    """Response for damage."""

    attacker: str
    target: str
    base_damage: int
    damage_type: str
    target_hp_before: int
    target_hp_after: int
    target_defeated: bool
    individual: list[int]
    dice_sizes: list[int]


class SpellTransformRequest(BaseModel):
    """Request to transform a spell."""

    encounter_id: str
    caster_id: str
    spell_name: str
    target_form: str
    seed: int | None = None


class SpellTransformResponse(BaseModel):
    """Response for a spell transformation."""

    spell: str
    target_form: str
    roll: int
    modifier: int
    total: int
    dc: int
    success: bool
    transformed: bool


class AdvanceTurnRequest(BaseModel):
    """Request to advance to the next turn."""

    encounter_id: str


class CheckEncounterOverResponse(BaseModel):
    """Response for checking if an encounter is over."""

    over: bool
    outcome: str | None


# ---------------------------------------------------------------------------
# Encounter API endpoints
# ---------------------------------------------------------------------------

@app.post("/encounters", response_model=EncounterResponse)
async def create_encounter(request: EncounterCreateRequest) -> EncounterResponse:
    """Create a new encounter with combatants."""
    enc = Encounter(
        name=request.name,
        description=request.description,
    )
    combatants: list[Combatant] = []
    for c in request.combatants:
        combatants.append(
            Combatant(
                id=c.id,
                name=c.name,
                type=c.type,
                strength=c.strength,
                dexterity=c.dexterity,
                constitution=c.constitution,
                intelligence=c.intelligence,
                wisdom=c.wisdom,
                charisma=c.charisma,
                ac=c.ac,
                hp=c.hp,
                max_hp=c.max_hp,
                damage_die=c.damage_die,
                damage_stat=c.damage_stat,
                damage_bonus=c.damage_bonus,
                weaknesses=c.weaknesses,
                resistances=c.resistances,
                immunities=c.immunities,
            )
        )
    enc.combatants = combatants
    encounter_id = f"enc_{len(encounters)}"
    encounters[encounter_id] = enc
    return _encounter_to_response(encounter_id, enc)


@app.get("/encounters/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(encounter_id: str) -> EncounterResponse:
    """Get an encounter by ID."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    return _encounter_to_response(encounter_id, enc)


@app.get("/encounters", response_model=list[EncounterResponse])
async def list_encounters() -> list[EncounterResponse]:
    """List all encounters."""
    return [_encounter_to_response(eid, enc) for eid, enc in encounters.items()]


@app.post("/encounters/{encounter_id}/turn-order", response_model=EncounterResponse)
async def set_turn_order(
    encounter_id: str,
    request: SetTurnOrderRequest,
) -> EncounterResponse:
    """Set the attack order for an encounter."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    encounter_manager.set_turn_order(enc, request.order)
    return _encounter_to_response(encounter_id, enc)


@app.post("/encounters/{encounter_id}/attack", response_model=AttackResponse)
async def resolve_attack(encounter_id: str, request: AttackRequest) -> AttackResponse:
    """Phase 2: Resolve an attack (hit or miss)."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    result = encounter_manager.resolve_attack(
        encounter=enc,
        attacker_id=request.attacker_id,
        target_id=request.target_id,
        attack_type=request.attack_type,
        dice_size=request.dice_size,
        seed=request.seed,
        advantage=request.advantage,
        disadvantage=request.disadvantage,
    )
    return AttackResponse(
        attacker=result["attacker"],
        target=result["target"],
        attack_type=result["attack_type"],
        roll=result["roll"],
        modifier=result["modifier"],
        total=result["total"],
        ac=result["ac"],
        hit=result["hit"],
        crit=result["crit"],
        target_stunned=result["target_stunned"],
        target_prone=result["target_prone"],
        target_blinded=result["target_blinded"],
    )


@app.post("/encounters/{encounter_id}/damage", response_model=DamageResponse)
async def resolve_damage(encounter_id: str, request: DamageRequest) -> DamageResponse:
    """Phase 4: Resolve damage."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    result = encounter_manager.resolve_damage(
        encounter=enc,
        attacker_id=request.attacker_id,
        target_id=request.target_id,
        attack_type=request.attack_type,
        damage_die=request.damage_die,
        damage_bonus=request.damage_bonus,
        seed=request.seed,
        extra_dice=request.extra_dice,
        extra_die_size=request.extra_die_size,
        critical=request.critical,
    )
    return DamageResponse(
        attacker=result["attacker"],
        target=result["target"],
        base_damage=result["base_damage"],
        damage_type=result["damage_type"],
        target_hp_before=result["target_hp_before"],
        target_hp_after=result["target_hp_after"],
        target_defeated=result["target_defeated"],
        individual=result["individual"],
        dice_sizes=result["dice_sizes"],
    )


@app.post("/encounters/{encounter_id}/status", response_model=StatusEffectResponse)
async def apply_status_effect(
    encounter_id: str,
    request: StatusEffectRequest,
) -> StatusEffectResponse:
    """Apply a status effect to a combatant."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    result = encounter_manager.apply_status_effect(
        encounter=enc,
        target_id=request.target_id,
        effect_name=request.effect_name,
        duration_rounds=request.duration_rounds,
        custom_description=request.custom_description,
    )
    return StatusEffectResponse(
        target=result["target"],
        effect=result["effect"],
        description=result["description"],
        duration_rounds=result["duration_rounds"],
        stunned=result["stunned"],
        prone=result["prone"],
        blinded=result["blinded"],
    )


@app.post("/encounters/{encounter_id}/spell-transform", response_model=SpellTransformResponse)
async def transform_spell(
    encounter_id: str,
    request: SpellTransformRequest,
) -> SpellTransformResponse:
    """Transform a spell on a successful roll (e.g. Lightning Bolt → Lightning Lasso)."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    result = encounter_manager.resolve_spell_transformation(
        encounter=enc,
        caster_id=request.caster_id,
        spell_name=request.spell_name,
        target_form=request.target_form,
        seed=request.seed,
    )
    return SpellTransformResponse(
        spell=result["spell"],
        target_form=result["target_form"],
        roll=result["roll"],
        modifier=result["modifier"],
        total=result["total"],
        dc=result["dc"],
        success=result["success"],
        transformed=result["transformed"],
    )


@app.post("/encounters/{encounter_id}/advance-turn", response_model=EncounterResponse)
async def advance_turn(encounter_id: str, request: AdvanceTurnRequest) -> EncounterResponse:
    """Advance to the next combatant's turn."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    encounter_manager.advance_turn(enc)
    return _encounter_to_response(encounter_id, enc)


@app.post("/encounters/{encounter_id}/check-over", response_model=CheckEncounterOverResponse)
async def check_encounter_over(encounter_id: str) -> CheckEncounterOverResponse:
    """Check if the encounter is over."""
    enc = encounters.get(encounter_id)
    if enc is None:
        raise HTTPException(status_code=404, detail="Encounter not found.")
    encounter_manager.check_encounter_over(enc)
    return CheckEncounterOverResponse(
        over=enc.over,
        outcome=enc.outcome,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _character_to_response(char: Character) -> CharacterResponse:
    return CharacterResponse(
        id=char.id,
        name=char.name,
        player_name=char.player_name,
        level=char.level,
        experience_points=char.experience_points,
        strength=char.strength,
        dexterity=char.dexterity,
        constitution=char.constitution,
        intelligence=char.intelligence,
        wisdom=char.wisdom,
        charisma=char.charisma,
        hit_points=char.hit_points,
        max_hit_points=char.max_hit_points,
        armor_class=char.armor_class,
        skills=list(char.skills),
        feats=list(char.feats),
        spells=list(char.spells),
        inventory=list(char.inventory),
        equipment=dict(char.equipment),
        created_at=char.created_at,
        updated_at=char.updated_at,
    )


def _combatant_to_response(c: Combatant) -> CombatantResponse:
    return CombatantResponse(
        id=c.id,
        name=c.name,
        type=c.type,
        strength=c.strength,
        dexterity=c.dexterity,
        constitution=c.constitution,
        intelligence=c.intelligence,
        wisdom=c.wisdom,
        charisma=c.charisma,
        ac=c.ac,
        hp=c.hp,
        max_hp=c.max_hp,
        damage_die=c.damage_die,
        damage_stat=c.damage_stat,
        damage_bonus=c.damage_bonus,
        weaknesses=list(c.weaknesses),
        resistances=list(c.resistances),
        immunities=list(c.inmunities),
        status_effects=[
            {
                "name": e.name,
                "description": e.description,
                "duration_rounds": e.duration_rounds,
                "stunned": e.stunned,
                "prone": e.prone,
                "blinded": e.blinded,
            }
            for e in c.status_effects
        ],
        achievements=[
            {
                "name": a.name,
                "description": a.description,
                "damage_bonus": a.damage_bonus,
                "damage_type": a.damage_type,
                "condition": a.condition,
            }
            for a in c.achievements
        ],
        current_action=c.current_action,
        defeated=c.defeated,
    )


def _encounter_to_response(encounter_id: str, enc: Encounter) -> EncounterResponse:
    return EncounterResponse(
        name=enc.name,
        description=enc.description,
        combatants=[_combatant_to_response(c) for c in enc.combatants],
        turn_order=list(enc.turn_order),
        current_turn_index=enc.current_turn_index,
        round=enc.round,
        over=enc.over,
        outcome=enc.outcome,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
