import { useState } from "react";
import { api } from "../api";
import type { StorySuggestRequest } from "../types";

function StorySuggester() {
  const [context, setContext] = useState("");
  const [dmNotes, setDmNotes] = useState("");
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const suggest = async () => {
    setLoading(true);
    setError(null);
    setSuggestion(null);
    try {
      const body: StorySuggestRequest = {
        current_context: context,
        dm_notes: dmNotes || undefined,
      };
      const data = await api.suggestStory(body);
      setSuggestion(data.suggestion);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Story Suggestions</h2>
        <span className="badge text-muted">LLM On-the-Fly</span>
      </div>
      <div className="card-body">
        <p className="muted">
          The LLM suggests story arcs, villains, surprises, clues, riddles, and
          NPCs based on the current story context.
        </p>
        <textarea
          className="btn secondary"
          placeholder="Current story context…"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          rows={3}
        />
        <textarea
          className="btn secondary"
          placeholder="DM notes (optional)…"
          value={dmNotes}
          onChange={(e) => setDmNotes(e.target.value)}
          rows={2}
        />
        <button className="btn primary" onClick={suggest} disabled={loading}>
          {loading ? "Suggesting…" : "Suggest Story"}
        </button>
        {error && <div className="error">{error}</div>}
        {suggestion && (
          <div className="run-row">
            <div className="run-details">{suggestion}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default StorySuggester;
