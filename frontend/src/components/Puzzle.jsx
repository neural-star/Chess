import React, { useEffect, useState } from "react";
import Board from "./Board";
import axios from "axios";

export default function Puzzle() {
  const [fen, setFen] = useState("startpos");
  const [solution, setSolution] = useState([]);
  const [input, setInput] = useState("");
  const [idx, setIdx] = useState(0);

  const load = async () => {
    const res = await axios.get("/puzzles/random");
    setFen(res.data.fen);
    setSolution(res.data.solution);
    setIdx(0);
    setInput("");
  };

  useEffect(load, []);

  const attempt = () => {
    if (input === solution[idx]) {
      setIdx(idx + 1);
      setFen((prev) => {
        // 次の一手を自動で反映
        const parts = prev.split(" ");
        const board = new Chess(parts[0]);
        board.move(input);
        return board.fen();
      });
      setInput("");
      if (idx + 1 === solution.length) {
        alert("正解！🎉");
      }
    } else {
      alert("不正解。もう一度。");
    }
  };

  return (
    <div className="p-4">
      <h2>詰将棋モード</h2>
      <Board fen={fen} />
      <div className="mt-2 flex">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="例：e7e8q"
          className="border p-1 flex-1"
        />
        <button onClick={attempt} className="ml-2 px-4 py-2 bg-green-500 text-white">
          試す
        </button>
        <button onClick={load} className="ml-2 px-4 py-2 bg-gray-300">
          新しい問題
        </button>
      </div>
    </div>
  );
}
