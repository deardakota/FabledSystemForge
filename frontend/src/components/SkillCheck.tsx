import { useState } from "react";
import { api } from "../api";
import type { SkillCheckRequest, SkillCheckResponse } from "../types";

function SkillCheck() {
  const [skillName, setSkillName] = useState("");
  const [statScore, setStatScore] = useState("10");
  const [dc, setDc] = useState("");
  const [result, setResult] = useState<SkillCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const check = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body: SkillCheckRequest = {
        skill_name: skillName,
        stat_score: Number(statScore) || 10,
        dc: dc ? Number(dc) : undefined,
      };
      const data = await api.skillCheck(body);
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
        <h2>Skill Check</h2>
        <span className="badge text-muted">d20 + Stat vs DC</span>
      </div>
      <div className="card-body">
        <p className="muted">
          Roll a d20, add the stat modifier, and compare to the difficulty
          class. This works for any skill check, puzzle, or trap.
        </p>
        <div className="actions">
          <input
            className="btn secondary"
            placeholder="Skill name (e.g. Stealth)"
            value={skillName}
            onChange={(e) => setSkillName(e.target.value)}
          />
          <input
            className="btn secondary"
            placeholder="Stat score (1–20)"
            type="number"
            min={1}
            max={20}
            value={statScore}
            onChange={(e) => setStatScore(e.target.value)}
          />
          <input
            className="btn secondary"
            placeholder="DC (optional)"
            type="number"
            value={dc}
            onChange={(e) => setDc(e.target.value)}
          />
          <button className="btn primary" onClick={check} disabled={loading}>
            {loading ? "Checking…" : "Resolve Check"}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
        {result && (
          <div className="run-row">
            <span className="run-details">
              <strong>{result.skill}</strong> ({result.stat} {result.modifier >= 0 ? "+" : ""}{result.modifier})
            </span>
            <span>
              Roll: {result.roll} + {result.modifier} = {result.total} vs DC {result.dc}
            </span>
            <span className={`badge ${result.passed ? "text-success" : "text-danger"}`}>
              {result.passed ? "Success" : "Failure"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default SkillCheck;
