import { useState } from "react";
import type { Combatant } from "../types";

function CombatantCard(props: {
  combatant: Combatant;
  onApplyEffect: (targetId: string, effectName: string) => void;
  isPlayer: boolean;
}) {
  const { combatant, onApplyEffect, isPlayer } = props;
  const [showEffects, setShowEffects] = useState(false);

  return (
    <div className={`card ${isPlayer ? "border-primary" : "border-danger"}`}>
      <div className="card-header">
        <h3>{combatant.name}</h3>
        <span className={`badge ${isPlayer ? "text-primary" : "text-danger"}`}>
          {combatant.type}
        </span>
      </div>
      <div className="card-body split">
        <div>
          <span className="btn secondary inline">STR: {combatant.strength}</span>
          <span className="btn secondary inline">DEX: {combatant.dexterity}</span>
          <span className="btn secondary inline">CON: {combatant.constitution}</span>
          <span className="btn secondary inline">INT: {combatant.intelligence}</span>
          <span className="btn secondary inline">WIS: {combatant.wisdom}</span>
          <span className="btn secondary inline">CHA: {combatant.charisma}</span>
        </div>
        <div>
          <p>AC: {combatant.ac}</p>
          <p>
            HP: {combatant.hp} / {combatant.max_hp}
          </p>
          <p>
            <strong>Damage:</strong> {combatant.damage_die} + {combatant.damage_bonus} ({combatant.damage_stat})
          </p>
        </div>
      </div>
      {combatant.status_effects?.length > 0 && (
        <div className="card-body">
          <strong>Effects:</strong>
          {combatant.status_effects.map((e, i) => (
            <span key={i} className="btn secondary inline">{e.name}</span>
          ))}
        </div>
      )}
      <button
        className="btn secondary"
        onClick={() => setShowEffects(true)}
      >
        {showEffects ? "Hide Effects" : "Add Effect"}
      </button>
      {showEffects && (
        <div className="card-body">
          <input
            className="btn secondary"
            placeholder="Effect name (blind, stun, prone, custom…)"
          />
          <button
            className="btn secondary"
            onClick={() => onApplyEffect(combatant.id, "stun")}
          >
            Apply Stun
          </button>
        </div>
      )}
    </div>
  );
}

export default CombatantCard;
