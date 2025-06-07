import React, { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import Board from "./Board";
import Clock from "./Clock";
import Chat from "./Chat";
import axios from "axios";

export default function GameView() {
  const { gameId } = useParams();
  const [fen, setFen] = useState("startpos");
  const [times, setTimes] = useState({ white: 0, black: 0 });
  const [move, setMove] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    // WebSocket 接続
    wsRef.current = new WebSocket(`ws://${window.location.host}/ws/game/${gameId}`);
    wsRef.current.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      setFen(data.fen);
      setTimes(data.times);
    };
    return () => wsRef.current.close();
  }, [gameId]);

  const sendMove = async () => {
    await axios.post("/pvp/move", {
      game_id: gameId,
      uci: move,
      player_color: data.whoseTurn, // フェッチした現在手番情報を渡す
    });
    setMove("");
  };

  return (
    <div className="flex flex-col md:flex-row">
      <div className="md:w-3/5 p-4">
        <Board fen={fen} />
        <div className="mt-2 flex">
          <input
            value={move}
            onChange={(e) => setMove(e.target.value)}
            placeholder="e2e4"
            className="border p-1 flex-1"
          />
          <button onClick={sendMove} className="ml-2 px-4 py-2 bg-blue-500 text-white">
            指す
          </button>
        </div>
      </div>
      <div className="md:w-2/5 p-4">
        <Clock times={times} />
        <Chat gameId={gameId} />
      </div>
    </div>
  );
}
