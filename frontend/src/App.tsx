import { useState } from "react";
import "./index.css";
import DiceRoller from "./components/DiceRoller";
import PlayerSheet from "./components/PlayerSheet";
import StorySuggester from "./components/StorySuggester";
import SystemGenerator from "./components/SystemGenerator";
import EncounterResolver from "./components/EncounterResolver";
import EnemySheetEditor from "./components/EnemySheetEditor";
import SpellTransformer from "./components/SpellTransformer";

function App() {
  const [view, setView] = useState<string>("system");

  return (
    <div className="app">
      <nav className="sidebar">
        <h1>Story Teller</h1>
        <div className="menu">
          <button
            className={`btn ${view === "home" ? "primary" : "secondary"}`}
            onClick={() => setView("home")}
          >
            Dashboard
          </button>
          <button
            className={`btn ${view === "players" ? "primary" : "secondary"}`}
            onClick={() => setView("players")}
          >
            Player Sheets
          </button>
          <button
            className={`btn ${view === "dice" ? "primary" : "secondary"}`}
            onClick={() => setView("dice")}
          >
            Dice Roller
          </button>
          <button
            className={`btn ${view === "story" ? "primary" : "secondary"}`}
            onClick={() => setView("story")}
          >
            Story/Suggestions
          </button>
          <button
            className={`btn ${view === "system" ? "primary" : "secondary"}`}
            onClick={() => setView("system")}
          >
            System Generator
          </button>
          <button
            className={`btn ${view === "combat" ? "primary" : "secondary"}`}
            onClick={() => setView("combat")}
          >
            Encounters
          </button>
          <button
            className={`btn ${view === "enemy" ? "primary" : "secondary"}`}
            onClick={() => setView("enemy")}
          >
            Enemy Sheets
          </button>
          <button
            className={`btn ${view === "spell" ? "primary" : "secondary"}`}
            onClick={() => setView("spell")}
          >
            Spell Transformer
          </button>
        </div>
      </nav>
      <main className="content">
        {view === "home" && <div>The Story Teller App</div>}
        {view === "players" && <PlayerSheet />}
        {view === "dice" && <DiceRoller />}
        {view === "story" && <StorySuggester />}
        {view === "system" && <SystemGenerator />}
        {view === "combat" && <EncounterResolver />}
        {view === "enemy" && <EnemySheetEditor />}
        {view === "spell" && <SpellTransformer />}
      </main>
    </div>
  );
}

export default App;
