import { useState } from "react";
import { api } from "../api";
import type { Combatant } from "../types";
import CombatantCard from "./CombatantCard";

function EncounterPage() {
  const [encounter, setEncounter] = useState<{
    id: string;
    name: string;
    description: string;
    combatants: Combatant[];
    turn_order: string[];
    current_turn_index: number;
    round: number;
    over: boolean;
    outcome: string | null;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCombatants, setShowCombatants] = useState(false);

  const createEncounter = async () => {
    setLoading(true);
    setError(null);
    try {
      const body = {
        name: "Test Encounter",
        description: "A test encounter.",
        combatants: [
          {
            id: "p1",
            name: "Rogue",
            type: "player",
            dexterity: 14,
            ac: 14,
            hp: 20,
            max_hp: 20,
            damage_die: 6,
            damage_stat: "dexterity",
            damage_bonus: 2,
            weaknesses: [],
            resistances: [],
            immunities: [],
          },
          {
            id: "e1",
            name: "Goblin",
            type: "enemy",
            strength: 12,
            ac: 13,
            hp: 10,
            max_hp: 10,
            damage_die: 6,
            damage_stat: "strength",
            damage_bonus: 1,
            weaknesses: [],
            resistances: [],
            immunities: [],
          },
        ],
      };
      const data = await api.createEncounter(body);
      setEncounter({
        id: data.name,
        name: data.name,
        description: data.description,
        combatants: data.combatants,
        turn_order: data.turn_order,
        current_turn_index: data.current_turn_index,
        round: data.round,
        over: data.over,
        outcome: data.outcome,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const resolveAttack = async (attackerId: string, targetId: string) => {
    if (!encounter) return;
    setLoading(true);
    try {
      const body = {
        encounter_id: encounter.id,
        attacker_id: attackerId,
        target_id: targetId,
        attack_type: "melee" as const,
        dice_size: 20,
      };
      await api.resolveAttack(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const resolveDamage = async (attackerId: string, targetId: string, damageDie: number) => {
    if (!encounter) return;
    setLoading(true);
    try {
      const body = {
        encounter_id: encounter.id,
        attacker_id: attackerId,
        target_id: targetId,
        attack_type: "melee",
        damage_die: damageDie,
        damage_bonus: 0,
        seed: null,
        extra_dice: 0,
        extra_die_size: 0,
        critical: false,
      };
      await api.resolveDamage(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const applyEffect = (targetId: string, effectName: string) => {
    if (!encounter) return;
    setLoading(true);
    try {
      api.applyStatusEffect({
        encounter_id: encounter.id,
        target_id: targetId,
        effect_name: effectName,
        duration_rounds: 2,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Encounter</h2>
        <button
          className={`btn ${showCombatants ? "secondary" : "primary"}`}
          onClick={() => setShowCombatants(!showCombatants)}
        >
          {showCombatants ? "Hide Combatants" : "Show Combatants"}
        </button>
      </div>
      <div className="card-body">
        {loading && <div>Loading…</div>}
        {error && <div className="error">{error}</div>}
        {!showCombatants && (
          <div>
            <p className="muted">
              Manage your encounter here. Set turn order, resolve attacks,
              apply damage, and track status effects.
            </p>
            <button className="btn primary" onClick={createEncounter}>
              Create Encounter
            </button>
          </div>
        )}
        {showCombatants && (
          <div>
            <h3>Combatants</h3>
            <div className="grid">
              {encounter && (
                <div>
                  {encounter.combatants.map((c) => (
                    <CombatantCard
                      key={c.id}
                      combatant={c}
                      onApplyEffect={(targetId, effectName) =>
                        applyEffect(targetId, effectName)}
                      isPlayer={c.type === "player"}
                    />
                  ))}
                </div>
              )}
            </div>
            <div className="actions">
              <button
                className="btn secondary"
                onClick={() =>
                  resolveAttack(
                    encounter!.combatants[0].id,
                    encounter!.combatants[1].id,
                  )
                }
              >
                Resolve Attack (P1 → E1)
              </button>
              <button
                className="btn primary"
                onClick={() =>
                  resolveDamage(
                    encounter!.combatants[0].id,
                    encounter!.combatants[1].id,
                    6,
                  )
                }
              >
                Deal Damage (1d6)
              </button>
              <button
                className="btn secondary"
                onClick={() => applyEffect(encounter!.combatants[1].id, "stun")}
              >
                Stun Enemy
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default EncounterPage;
