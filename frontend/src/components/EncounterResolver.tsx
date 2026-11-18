import { useState } from "react";
import { api } from "../api";

type SystemEncounterResponse = {
  encounter: string;
  enemy: string;
  enemy_hp: number;
  enemy_ac: number;
  player_roll: number;
  enemy_roll: number;
  player_success: boolean;
  narrative: string;
};

function EncounterResolver() {
  const [encounterName, setEncounterName] = useState("");
  const [actions, setActions] = useState("");
  const [result, setResult] = useState<SystemEncounterResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resolve = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body = {
        encounter_name: encounterName,
        player_actions: actions
          .split("\n")
          .map((a) => a.trim())
          .filter((a) => a.length > 0),
      };
      const data = await api.resolveEncounter(body);
      setResult(data as SystemEncounterResponse);
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
        <span className="badge text-muted">Dice-Driven Combat</span>
      </div>
      <div className="card-body">
        <p className="muted">
          Resolve an encounter. The dice determine success/failure and the LLM
          narrates the outcome.
        </p>
        <input
          className="btn secondary"
          placeholder="Encounter name (e.g. Goblin Camp)"
          value={encounterName}
          onChange={(e) => setEncounterName(e.target.value)}
        />
        <textarea
          className="btn secondary"
          placeholder="Player actions (one per line)…"
          value={actions}
          onChange={(e) => setActions(e.target.value)}
          rows={3}
        />
        <button className="btn primary" onClick={resolve} disabled={loading}>
          {loading ? "Resolving…" : "Resolve Encounter"}
        </button>
        {error && <div className="error">{error}</div>}
        {result && (
          <>
            <div className="run-row">
              <span className="run-details">
                <strong>Encounter:</strong> {result.encounter} — {result.enemy} (HP {result.enemy_hp}, AC {result.enemy_ac})
              </span>
              <span>
                Player: {result.player_roll} | Enemy: {result.enemy_roll}
              </span>
              <span className={`badge ${result.player_success ? "text-success" : "text-danger"}`}>
                {result.player_success ? "Players prevail" : "Enemy prevails"}
              </span>
            </div>
            <div className="run-details">{result.narrative}</div>
          </>
        )}
      </div>
    </div>
  );
}

export default EncounterResolver;
