import { useState } from "react";
import { api } from "../api";
import type { SpellTransformRequest, SpellTransformResponse } from "../types";

function SpellTransformer() {
  const [encounterId, setEncounterId] = useState("");
  const [casterId, setCasterId] = useState("");
  const [spellName, setSpellName] = useState("Lightning Bolt");
  const [targetForm, setTargetForm] = useState("Lightning Lasso");
  const [result, setResult] = useState<SpellTransformResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const transform = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body: SpellTransformRequest = {
        encounter_id: encounterId,
        caster_id: casterId,
        spell_name: spellName,
        target_form: targetForm,
      };
      const data = await api.transformSpell(body);
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
        <h2>Spell Transformer</h2>
        <span className="badge text-muted">Transform spells on a successful roll</span>
      </div>
      <div className="card-body">
        <p className="muted">
          The caster rolls a d20 + Wisdom modifier vs DC 15. On success, the
          spell transforms into the target form for the rest of the encounter.
        </p>
        <input
          className="btn secondary"
          placeholder="Encounter ID"
          value={encounterId}
          onChange={(e) => setEncounterId(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="Caster ID"
          value={casterId}
          onChange={(e) => setCasterId(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="Spell name (e.g. Lightning Bolt)"
          value={spellName}
          onChange={(e) => setSpellName(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="Target form (e.g. Lightning Lasso)"
          value={targetForm}
          onChange={(e) => setTargetForm(e.target.value)}
        />
        <button
          className="btn primary"
          onClick={transform}
          disabled={loading}
        >
          {loading ? "Transforming…" : "Attempt Transformation"}
        </button>
        {error && <div className="error">{error}</div>}
        {result && (
          <div className="run-row">
            <span className="run-details">
              {result.spell} → {result.target_form}
            </span>
            <span>
              Roll: {result.roll} + {result.modifier} = {result.total} vs DC {result.dc}
            </span>
            <span className={`badge ${result.success ? "text-success" : "text-danger"}`}>
              {result.success ? "Transformed!" : "Failed"}
            </span>
            {result.transformed && (
              <span>Spell is now {result.target_form} for the encounter.</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default SpellTransformer;
