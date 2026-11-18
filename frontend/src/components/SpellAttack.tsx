import { useState } from "react";
import { api } from "../api";
import type { SpellAttackRequest, SpellAttackResponse } from "../types";

function SpellAttack() {
  const [spellName, setSpellName] = useState("");
  const [attackStat, setAttackStat] = useState("10");
  const [targetAC, setTargetAC] = useState("12");
  const [result, setResult] = useState<SpellAttackResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const attack = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body: SpellAttackRequest = {
        spell_name: spellName,
        attack_stat_score: Number(attackStat) || 10,
        target_ac: Number(targetAC) || 12,
      };
      const data = await api.spellAttack(body);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Spell Attack</h2>
        <span className="badge text-muted">d20 + Stat vs AC</span>
      </div>
      <div className="card-body">
        <p className="muted">
          Roll a d20, add the stat modifier, and compare to the target AC. On
          a hit, roll damage.
        </p>
        <div className="actions">
          <input
            className="btn secondary"
            placeholder="Spell name (e.g. Fireball)"
            value={spellName}
            onChange={(e) => setSpellName(e.target.value)}
          />
          <input
            className="btn secondary"
            placeholder="Attack stat (1–20)"
            type="number"
            min={1}
            max={20}
            value={attackStat}
            onChange={(e) => setAttackStat(e.target.value)}
          />
          <input
            className="btn secondary"
            placeholder="Target AC"
            type="number"
            value={targetAC}
            onChange={(e) => setTargetAC(e.target.value)}
          />
          <button className="btn primary" onClick={attack} disabled={loading}>
            {loading ? "Attacking…" : "Resolve Attack"}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
        {result && (
          <div className="run-row">
            <span className="run-details">
              <strong>{result.spell}</strong> — roll {result.roll} + {result.modifier} = {result.total} vs AC {result.ac}
            </span>
            <span className={`badge ${result.hit ? "text-success" : "text-danger"}`}>
              {result.hit ? "Hit" : "Miss"}
            </span>
            {result.hit && (
              <span>
                Damage: {result.damage} ({result.damage_details.join(", ")})
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default SpellAttack;
