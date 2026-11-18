import type {
  AttackRequest,
  AttackResponse,
  CombatSuggestRequest,
  CombatSuggestResponse,
  Character,
  CreateCharacterRequest,
  DamageRequest,
  DamageResponse,
  DiceRollResult,
  DiceSize,
  EncounterCreateRequest,
  EncounterResponse,
  LLMStatus,
  NPCSuggestRequest,
  NPCSuggestResponse,
  SkillCheckRequest,
  SkillCheckResponse,
  SpellAttackRequest,
  SpellAttackResponse,
  SetTurnOrderRequest,
  SpellTransformRequest,
  SpellTransformResponse,
  StorySuggestRequest,
  StorySuggestResponse,
  StatusEffectRequest,
  StatusEffectResponse,
  SystemGenerateRequest,
  SystemGenerateResponse,
  UpdateCharacterRequest,
} from "./types";

const API_BASE = "http://127.0.0.1:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${await response.text()}`);
  }
  return (await response.json()) as T;
}

export const api = {
  getHealth: () => fetchJson<{ status: string; service: string }>("/health"),

  getLlmStatus: () => fetchJson<LLMStatus>("/llm/status"),

  rollDice: (body: {
    dice_sizes: DiceSize[];
    seed?: number | null;
    advantage?: boolean;
    disadvantage?: boolean;
  }) => fetchJson<DiceRollResult>("/dice/roll", {
    method: "POST",
    body: JSON.stringify(body),
  }),

  compareRoll: (body: { total: number; target: number }) =>
    fetchJson<{ result: "success" | "failure" | "critical" }>(
      "/dice/compare",
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  listPlayers: () => fetchJson<Character[]>("/players"),

  createPlayer: (body: CreateCharacterRequest) =>
    fetchJson<Character>("/players", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getPlayer: (id: string) => fetchJson<Character>(`/players/${id}`),

  updatePlayer: (id: string, body: UpdateCharacterRequest) =>
    fetchJson<Character>(`/players/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  deletePlayer: (id: string) =>
    fetchJson<{ status: string; id: string }>(`/players/${id}`, {
      method: "DELETE",
    }),

  suggestStory: (body: StorySuggestRequest) =>
    fetchJson<StorySuggestResponse>("/llm/suggest-story", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  suggestCombat: (body: CombatSuggestRequest) =>
    fetchJson<CombatSuggestResponse>("/llm/suggest-combat", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  suggestNpc: (body: NPCSuggestRequest) =>
    fetchJson<NPCSuggestResponse>("/llm/suggest-npc", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  generateSystem: (body: SystemGenerateRequest) =>
    fetchJson<SystemGenerateResponse>("/system/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  skillCheck: (body: SkillCheckRequest) =>
    fetchJson<SkillCheckResponse>("/system/skill-check", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  spellAttack: (body: SpellAttackRequest) =>
    fetchJson<SpellAttackResponse>("/system/spell-attack", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  resolveEncounter: (body: {
    encounter_name: string;
    player_actions?: string[];
    seed?: number | null;
  }) =>
    fetchJson<{
      encounter: string;
      enemy: string;
      enemy_hp: number;
      enemy_ac: number;
      player_roll: number;
      enemy_roll: number;
      player_success: boolean;
      narrative: string;
    }>("/system/encounter", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // ---------- Encounter / Combat ----------

  createEncounter: (body: EncounterCreateRequest) =>
    fetchJson<EncounterResponse>("/encounters", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getEncounter: (encounterId: string) =>
    fetchJson<EncounterResponse>(`/encounters/${encounterId}`),

  listEncounters: () => fetchJson<EncounterResponse[]>("/encounters"),

  setTurnOrder: (body: SetTurnOrderRequest) =>
    fetchJson<EncounterResponse>(
      `/encounters/${body.encounter_id}/turn-order`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  resolveAttack: (body: AttackRequest) =>
    fetchJson<AttackResponse>(
      `/encounters/${body.encounter_id}/attack`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  resolveDamage: (body: DamageRequest) =>
    fetchJson<DamageResponse>(
      `/encounters/${body.encounter_id}/damage`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  applyStatusEffect: (body: StatusEffectRequest) =>
    fetchJson<StatusEffectResponse>(
      `/encounters/${body.encounter_id}/status`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  transformSpell: (body: SpellTransformRequest) =>
    fetchJson<SpellTransformResponse>(
      `/encounters/${body.encounter_id}/spell-transform`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  advanceTurn: (body: { encounter_id: string }) =>
    fetchJson<EncounterResponse>(
      `/encounters/${body.encounter_id}/advance-turn`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),

  checkEncounterOver: (body: { encounter_id: string }) =>
    fetchJson<{
      over: boolean;
      outcome: string | null;
    }>(
      `/encounters/${body.encounter_id}/check-over`,
      {
        method: "POST",
        body: JSON.stringify(body),
      }
    ),
};
