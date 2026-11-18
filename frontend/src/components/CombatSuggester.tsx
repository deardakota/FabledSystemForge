import { useState } from "react";
import { api } from "../api";
import type { CombatSuggestRequest, DiceSize } from "../types";

function CombatSuggester() {
  const [encounter, setEncounter] = useState("");
  const [enemy, setEnemy] = useState("");
  const [actions, setActions] = useState("");
  const [diceSizes] = useState<DiceSize[]>([20]);
  const [suggestion, setSuggestion] = useState<{
    suggestion: string;
    dice_roll: {
      total: number;
      individual: number[];
    };
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const suggest = async () => {
    setLoading(true);
    setError(null);
    setSuggestion(null);
    try {
      const body: CombatSuggestRequest = {
        encounter_description: encounter,
        enemy_description: enemy || undefined,
        player_actions: actions
          .split("\n")
          .map((a) => a.trim())
          .filter((a) => a.length > 0),
        dice_sizes: diceSizes,
        advantage: false,
        disadvantage: false,
      };
      const data = await api.suggestCombat(body);
      setSuggestion({
        suggestion: data.suggestion,
        dice_roll: {
          total: data.dice_roll.total,
          individual: data.dice_roll.individual,
        },
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
        <h2>Combat Outcome</h2>
        <span className="badge text-muted">Dice-Driven Narration</span>
      </div>
      <div className="card-body">
        <p className="muted">
          The dice roll is the source of truth for success or failure. The LLM
          narrates the outcome accordingly.
        </p>
        <textarea
          className="btn secondary"
          placeholder="Encounter description…"
          value={encounter}
          onChange={(e) => setEncounter(e.target.value)}
          rows={2}
        />
        <textarea
          className="btn secondary"
          placeholder="Enemy description…"
          value={enemy}
          onChange={(e) => setEnemy(e.target.value)}
          rows={2}
        />
        <textarea
          className="btn secondary"
          placeholder="Player actions (one per line)…"
          value={actions}
          onChange={(e) => setActions(e.target.value)}
          rows={3}
        />
        <div className="muted">{`Dice: ${diceSizes.map((s) => `d${s}`).join(", ")}`}</div>
        <button className="btn primary" onClick={suggest} disabled={loading}>
          {loading ? "Narrating…" : "Narrate Outcome"}
        </button>
        {error && <div className="error">{error}</div>}
        {suggestion && (
          <div className="run-row">
            <span className="run-details">
              <strong>Roll:</strong> {suggestion.dice_roll.total}
              ({suggestion.dice_roll.individual.join(", ")})
            </span>
            <div className="run-details">{suggestion.suggestion}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CombatSuggester;
