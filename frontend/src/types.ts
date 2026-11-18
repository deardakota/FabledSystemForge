export type DiceSize = 4 | 6 | 8 | 10 | 12 | 20 | 100;

export interface DiceRollResult {
  total: number;
  individual: number[];
  dice_sizes: DiceSize[];
  seed?: number | null;
}

export interface CompareRollResponse {
  result: "success" | "failure" | "critical";
}

export interface Character {
  id: string;
  name: string;
  player_name: string;
  level: number;
  experience_points: number;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  hit_points: number;
  max_hit_points: number;
  armor_class: number;
  skills: string[];
  feats: string[];
  spells: string[];
  inventory: string[];
  equipment: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface CreateCharacterRequest {
  name: string;
  player_name: string;
  level?: number;
  stats?: Record<string, number>;
}

export interface UpdateCharacterRequest {
  name?: string;
  player_name?: string;
  level?: number;
  experience_points?: number;
  strength?: number;
  dexterity?: number;
  constitution?: number;
  intelligence?: number;
  wisdom?: number;
  charisma?: number;
  hit_points?: number;
  max_hit_points?: number;
  armor_class?: number;
  skills?: string[];
  feats?: string[];
  spells?: string[];
  inventory?: string[];
  equipment?: Record<string, string>;
}

export interface StorySuggestRequest {
  current_context: string;
  player_characters?: string[];
  dm_notes?: string;
}

export interface StorySuggestResponse {
  suggestion: string;
  confidence: number;
  dice_roll?: DiceRollResult;
}

export interface CombatSuggestRequest {
  encounter_description: string;
  player_actions?: string[];
  dice_sizes?: DiceSize[];
  seed?: number | null;
  advantage?: boolean;
  disadvantage?: boolean;
  enemy_description?: string;
}

export interface CombatSuggestResponse {
  suggestion: string;
  confidence: number;
  dice_roll: DiceRollResult;
}

export interface NPCSuggestRequest {
  name: string;
  role: string;
  context: string;
}

export interface NPCSuggestResponse {
  suggestion: string;
  confidence: number;
}

export interface LLMStatus {
  available: boolean;
  model: string;
  base_url: string;
}

// --- System generator types ---

export interface SkillEntry {
  name: string;
  description: string;
  stat: string;
  die_size?: number;
  difficulty_class?: number;
}

export interface SpellEntry {
  name: string;
  description: string;
  level?: number;
  die_size?: number;
  damage_die?: number;
  damage_stat?: string;
}

export interface FeatEntry {
  name: string;
  description: string;
  prerequisite?: string;
}

export interface EncounterTemplate {
  name: string;
  description: string;
  enemy_name: string;
  enemy_hp: number;
  enemy_ac: number;
  enemy_die_size?: number;
  objective?: string;
}

export interface SystemGenerateRequest {
  story_context: string;
  theme?: string;
  player_characters?: string[];
  dm_notes?: string;
}

export interface SystemGenerateResponse {
  name: string;
  theme: string;
  description: string;
  skills: SkillEntry[];
  spells: SpellEntry[];
  feats: FeatEntry[];
  encounters: EncounterTemplate[];
  default_dc: number;
}

export interface SkillCheckRequest {
  skill_name: string;
  stat_score: number;
  dc?: number;
  seed?: number | null;
}

export interface SkillCheckResponse {
  skill: string;
  stat: string;
  stat_score: number;
  modifier: number;
  roll: number;
  total: number;
  dc: number;
  passed: boolean;
  individual: number[];
}

export interface SpellAttackRequest {
  spell_name: string;
  attack_stat_score: number;
  target_ac: number;
  seed?: number | null;
}

export interface SpellAttackResponse {
  spell: string;
  roll: number;
  modifier: number;
  total: number;
  ac: number;
  hit: boolean;
  damage: number;
  damage_details: string[];
  individual: number[];
}

// --- Encounter / combat types ---

export interface StatusEffect {
  name: string;
  description: string;
  duration_rounds: number;
  stacks?: boolean;
  ac_penalty?: number;
  attack_penalty?: number;
  movement_penalty?: number;
  stunned?: boolean;
  prone?: boolean;
  blinded?: boolean;
}

export interface Achievement {
  name: string;
  description: string;
  damage_bonus?: number;
  damage_type?: string;
  attack_bonus?: number;
  ac_bonus?: number;
  movement_bonus?: number;
  condition?: string;
}

export interface EnemySheet {
  name: string;
  description: string;
  hp: number;
  max_hp: number;
  ac: number;
  strength?: number;
  dexterity?: number;
  constitution?: number;
  intelligence?: number;
  wisdom?: number;
  charisma?: number;
  damage_die?: number;
  damage_stat?: string;
  damage_bonus?: number;
  weaknesses?: string[];
  resistances?: string[];
  immunities?: string[];
  spells?: string[];
  skills?: string[];
  status_effects?: StatusEffect[];
  achievements?: Achievement[];
  defeated?: boolean;
}

export interface Combatant {
  id: string;
  name: string;
  type: string;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  ac: number;
  hp: number;
  max_hp: number;
  damage_die: number;
  damage_stat: string;
  damage_bonus: number;
  weaknesses: string[];
  resistances: string[];
  immunities: string[];
  status_effects: StatusEffect[];
  achievements: Achievement[];
  current_action: string | null;
  defeated: boolean;
}

export interface CombatantRequest {
  id: string;
  name: string;
  type: string;
  strength?: number;
  dexterity?: number;
  constitution?: number;
  intelligence?: number;
  wisdom?: number;
  charisma?: number;
  ac?: number;
  hp?: number;
  max_hp?: number;
  damage_die?: number;
  damage_stat?: string;
  damage_bonus?: number;
  weaknesses?: string[];
  resistances?: string[];
  immunities?: string[];
}

export interface Encounter {
  name: string;
  description: string;
  combatants: Combatant[];
  turn_order: string[];
  current_turn_index: number;
  round: number;
  over: boolean;
  outcome: string | null;
}

export interface EncounterCreateRequest {
  name: string;
  description: string;
  combatants: CombatantRequest[];
}

export interface EncounterResponse {
  name: string;
  description: string;
  combatants: Combatant[];
  turn_order: string[];
  current_turn_index: number;
  round: number;
  over: boolean;
  outcome: string | null;
}

export interface SetTurnOrderRequest {
  encounter_id: string;
  order: string[];
}

export interface AttackRequest {
  encounter_id: string;
  attacker_id: string;
  target_id: string;
  attack_type: "melee" | "ranged" | "spell";
  dice_size: number;
  seed?: number | null;
  advantage?: boolean;
  disadvantage?: boolean;
}

export interface AttackResponse {
  attacker: string;
  target: string;
  attack_type: string;
  roll: number;
  modifier: number;
  total: number;
  ac: number;
  hit: boolean;
  crit: boolean;
  target_stunned: boolean;
  target_prone: boolean;
  target_blinded: boolean;
}

export interface DamageRequest {
  encounter_id: string;
  attacker_id: string;
  target_id: string;
  attack_type: string;
  damage_die: number;
  damage_bonus: number;
  seed?: number | null;
  extra_dice: number;
  extra_die_size: number;
  critical: boolean;
}

export interface DamageResponse {
  attacker: string;
  target: string;
  base_damage: number;
  damage_type: string;
  target_hp_before: number;
  target_hp_after: number;
  target_defeated: boolean;
  individual: number[];
  dice_sizes: number[];
}

export interface StatusEffectRequest {
  encounter_id: string;
  target_id: string;
  effect_name: string;
  duration_rounds: number;
  custom_description?: string;
}

export interface StatusEffectResponse {
  target: string;
  effect: string;
  description: string;
  duration_rounds: number;
  stunned: boolean;
  prone: boolean;
  blinded: boolean;
}

export interface SpellTransformRequest {
  encounter_id: string;
  caster_id: string;
  spell_name: string;
  target_form: string;
  seed?: number | null;
}

export interface SpellTransformResponse {
  spell: string;
  target_form: string;
  roll: number;
  modifier: number;
  total: number;
  dc: number;
  success: boolean;
  transformed: boolean;
}

export interface AdvanceTurnRequest {
  encounter_id: string;
}

export interface CheckEncounterOverResponse {
  over: boolean;
  outcome: string | null;
}
