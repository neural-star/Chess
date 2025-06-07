import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Lobby       from "./components/Lobby";
import GameView    from "./components/GameView";
import AuthForm    from "./components/AuthForm";
import Puzzle      from "./components/Puzzle";
import Analysis    from "./components/AnalysisPanel";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthForm />} />
        <Route path="/lobby" element={<Lobby />} />
        <Route path="/game/:gameId" element={<GameView />} />
        <Route path="/puzzle" element={<Puzzle />} />
        <Route path="/analysis" element={<Analysis />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
