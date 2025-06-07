import React, { useEffect, useState, useRef } from "react";

export default function Chat({ gameId }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(`ws://${window.location.host}/ws/chat/${gameId}`);
    ws.current.onmessage = (ev) => {
      setMsgs((prev) => [...prev, ev.data]);
    };
    return () => ws.current.close();
  }, [gameId]);

  const send = () => {
    ws.current.send(input);
    setInput("");
  };

  return (
    <div className="border p-2 h-96 flex flex-col">
      <div className="flex-1 overflow-y-auto">
        {msgs.map((m, i) => (
          <div key={i} className="mb-1">{m}</div>
        ))}
      </div>
      <div className="mt-2 flex">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="border p-1 flex-1"
          placeholder="チャット入力…"
        />
        <button onClick={send} className="ml-2 px-3 bg-gray-800 text-white">
          送信
        </button>
      </div>
    </div>
  );
}

