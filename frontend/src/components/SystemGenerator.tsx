import { useState } from "react";
import { api } from "../api";
import type {
  SystemGenerateRequest,
  SystemGenerateResponse,
} from "../types";

function SystemGenerator() {
  const [context, setContext] = useState("");
  const [theme, setTheme] = useState("");
  const [dmNotes, setDmNotes] = useState("");
  const [profile, setProfile] = useState<SystemGenerateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    setProfile(null);
    try {
      const body: SystemGenerateRequest = {
        story_context: context,
        theme: theme || undefined,
        player_characters: [],
        dm_notes: dmNotes || undefined,
      };
      const data = await api.generateSystem(body);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  if (!profile) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>System Generator</h2>
          <span className="badge text-muted">Session Mechanic Profile</span>
        </div>
        <div className="card-body">
          <p className="muted">
            Generate a bespoke mechanic system (skills, spells, feats,
            encounters) for this story session. Everything resolves through
            polyhedral dice — the only rigid mechanic.
          </p>
          <textarea
            className="btn secondary"
            placeholder="Story context…"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            rows={3}
          />
          <textarea
            className="btn secondary"
            placeholder="Theme (e.g. fantasy heist, cyberpunk, gothic)…"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            rows={2}
          />
          <textarea
            className="btn secondary"
            placeholder="DM notes (optional)…"
            value={dmNotes}
            onChange={(e) => setDmNotes(e.target.value)}
            rows={2}
          />
          <button className="btn primary" onClick={generate} disabled={loading}>
            {loading ? "Generating…" : "Generate System"}
          </button>
          {error && <div className="error">{error}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>System: {profile.name}</h2>
        <span className="badge text-muted">{profile.theme}</span>
      </div>
      <div className="card-body">
        <p>{profile.description}</p>

        <div className="muted">
          <strong>Skills:</strong>
          {profile.skills.map((s, i) => (
            <span key={i} className="btn secondary inline">{s.name}</span>
          ))}
        </div>
        <div className="muted">
          <strong>Spells:</strong>
          {profile.spells.map((s, i) => (
            <span key={i} className="btn secondary inline">{s.name}</span>
          ))}
        </div>
        <div className="muted">
          <strong>Feats:</strong>
          {profile.feats.map((f, i) => (
            <span key={i} className="btn secondary inline">{f.name}</span>
          ))}
        </div>
        <div className="muted">
          <strong>Encounters:</strong>
          {profile.encounters.map((e, i) => (
            <span key={i} className="btn secondary inline">{e.name}</span>
          ))}
        </div>

        <button className="btn secondary" onClick={generate}>
          Regenerate System
        </button>
      </div>
    </div>
  );
}

export default SystemGenerator;
