import { useState } from "react";
import { api } from "../api";
import type { DiceSize } from "../types";

const AVAILABLE_DICE: DiceSize[] = [4, 6, 8, 10, 12, 20, 100];

function DiceRoller() {
  const [diceSizes, setDiceSizes] = useState<DiceSize[]>([20]);
  const [result, setResult] = useState<{
    total: number;
    individual: number[];
    dice_sizes: DiceSize[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRoll = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.rollDice({
        dice_sizes: diceSizes,
        advantage: false,
        disadvantage: false,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const toggleDie = (size: DiceSize) => {
    setDiceSizes((prev) =>
      prev.includes(size)
        ? prev.filter((s) => s !== size)
        : [...prev, size]
    );
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Dice Roller</h2>
        <span className="badge text-muted">Polyhedral Dice</span>
      </div>
      <div className="card-body">
        <p className="muted">
          The only rigid mechanic is polyhedral dice (d20, d10, etc.) for player
          interactions.
        </p>
        <div className="actions">
          {AVAILABLE_DICE.map((size) => (
            <button
              key={size}
              onClick={() => toggleDie(size)}
              className={`btn ${
                diceSizes.includes(size) ? "primary" : "secondary"
              }`}
            >
              d{size}
            </button>
          ))}
        </div>
        <div className="muted">
          {`Dice: ${diceSizes.map((s) => `d${s}`).join(", ")}`}
        </div>
        <button
          className="btn primary"
          onClick={handleRoll}
          disabled={loading}
        >
          {loading ? "Rolling…" : "Roll Dice"}
        </button>
        {error && <div className="error">{error}</div>}
        {result && (
          <div className="run-row">
            <span className="run-details">
              <strong>Total:</strong> {result.total}
            </span>
            <span>
              Individual: {result.individual.join(", ")}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default DiceRoller;
