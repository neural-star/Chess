import React, { useState } from "react";
import axios from "axios";

export default function AnalysisPanel() {
  const [movesText, setMovesText] = useState("");
  const [imgSrc, setImgSrc] = useState(null);

  const analyze = async () => {
    const moves = movesText.trim().split(/\s+/);
    const res = await axios.post("/analysis/eval", { moves }, { responseType: "blob" });
    setImgSrc(URL.createObjectURL(res.data));
  };

  return (
    <div className="p-4">
      <h2>局面解析モード</h2>
      <textarea
        value={movesText}
        onChange={(e) => setMovesText(e.target.value)}
        placeholder="e2e4 e7e5 g1f3 …"
        className="w-full h-24 border p-2"
      />
      <button onClick={analyze} className="mt-2 px-4 py-2 bg-blue-600 text-white">
        解析
      </button>
      {imgSrc && (
        <div className="mt-4">
          <img src={imgSrc} alt="評価グラフ" />
        </div>
      )}
    </div>
  );
}
