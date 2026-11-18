import { useState, useEffect } from "react";
import { api } from "../api";
import type { CreateCharacterRequest, Character } from "../types";

function PlayerSheet() {
  const [players, setPlayers] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create form state
  const [name, setName] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [level, setLevel] = useState("1");

  const loadPlayers = async () => {
    try {
      const data = await api.listPlayers();
      setPlayers(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const createPlayer = async () => {
    setError(null);
    try {
      const body: CreateCharacterRequest = {
        name,
        player_name: playerName,
        level: Number(level) || 1,
      };
      const data = await api.createPlayer(body);
      setPlayers((prev) => [data, ...prev]);
      // Reset form
      setName("");
      setPlayerName("");
      setLevel("1");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  useEffect(() => {
    loadPlayers();
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <h2>Player Sheets</h2>
        <span className="badge text-muted">Character Stats</span>
      </div>
      <div className="card-body">
        <div className="actions">
          <input
            className="btn secondary"
            placeholder="Character name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="btn secondary"
            placeholder="Player name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
          />
          <input
            className="btn secondary"
            placeholder="Level"
            type="number"
            value={level}
            onChange={(e) => setLevel(e.target.value)}
          />
          <button className="btn primary" onClick={createPlayer}>
            Create Character
          </button>
        </div>
        {error && <div className="error">{error}</div>}
        {loading ? (
          <div className="loading">Loading players…</div>
        ) : players.length === 0 ? (
          <div className="empty">No characters yet. Create one above.</div>
        ) : (
          <table className="deal-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Player</th>
                <th>Level</th>
                <th>Str</th>
                <th>Dex</th>
                <th>Con</th>
                <th>Int</th>
                <th>Wis</th>
                <th>Cha</th>
                <th>HP</th>
                <th>AC</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.player_name}</td>
                  <td>{p.level}</td>
                  <td>{p.strength}</td>
                  <td>{p.dexterity}</td>
                  <td>{p.constitution}</td>
                  <td>{p.intelligence}</td>
                  <td>{p.wisdom}</td>
                  <td>{p.charisma}</td>
                  <td>{p.hit_points}</td>
                  <td>{p.armor_class}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default PlayerSheet;
