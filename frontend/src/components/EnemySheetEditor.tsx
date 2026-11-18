import { useState } from "react";
import type { EnemySheet } from "../types";

function EnemySheetEditor() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [hp, setHp] = useState("10");
  const [ac, setAc] = useState("12");
  const [damageDie, setDamageDie] = useState("6");
  const [damageStat, setDamageStat] = useState("strength");
  const [weaknesses, setWeaknesses] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createEnemy = async () => {
    setLoading(true);
    setError(null);
    try {
      const body: EnemySheet = {
        name,
        description,
        hp: Number(hp) || 10,
        max_hp: Number(hp) || 10,
        ac: Number(ac) || 12,
        damage_die: Number(damageDie) || 6,
        damage_stat: damageStat,
        damage_bonus: 0,
        weaknesses: weaknesses.split(",").map((w) => w.trim()).filter(Boolean),
        resistances: [],
        immunities: [],
        spells: [],
        skills: [],
        status_effects: [],
        achievements: [],
        defeated: false,
      };
      console.log("Creating enemy sheet:", body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Enemy Sheet</h2>
        <span className="badge text-muted">Tailor enemies on the fly</span>
      </div>
      <div className="card-body">
        <p className="muted">
          Create an enemy sheet with stats, weaknesses, resistances, spells,
          and skills. The DM fills these out before or during the encounter.
        </p>
        <input
          className="btn secondary"
          placeholder="Name (e.g. Goblin)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="HP"
          type="number"
          value={hp}
          onChange={(e) => setHp(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="AC"
          type="number"
          value={ac}
          onChange={(e) => setAc(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="Damage die (4, 6, 8, 10, 12, 20)"
          type="number"
          value={damageDie}
          onChange={(e) => setDamageDie(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="Damage stat (strength/dexterity)"
          value={damageStat}
          onChange={(e) => setDamageStat(e.target.value)}
        />
        <input
          className="btn secondary"
          placeholder="Weaknesses (comma-separated)"
          value={weaknesses}
          onChange={(e) => setWeaknesses(e.target.value)}
        />
        <button className="btn primary" onClick={createEnemy} disabled={loading}>
          {loading ? "Creating…" : "Create Enemy Sheet"}
        </button>
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  );
}

export default EnemySheetEditor;
