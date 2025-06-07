import React, { useState } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";

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

export default function AnalysisPanel() {
  const [movesText, setMovesText] = useState("");
  const [data, setData]       = useState(null);

  const analyze = async () => {
    const moves = movesText.trim().split(/\s+/);
    const res = await axios.post("/analysis/compare", moves);
    setData({
      labels: moves.map((m,i) => `${i+1}.${m}`),
      datasets: [
        {
          label: "あなたの評価",
          data: res.data.actual_eval,
          borderDash: [],  // 実線
        },
        {
          label: "エンジン最善手",
          data: res.data.best_eval,
          borderDash: [5,5],  // 破線
        }
      ]
    });
  };

  return (
    <div>
      <h2>評価比較グラフ</h2>
      <textarea
        value={movesText}
        onChange={(e) => setMovesText(e.target.value)}
        placeholder="e2e4 e7e5 g1f3 …"
        className="w-full h-24 border p-2"
      />
      <button onClick={analyze} className="mt-2 px-4 py-2 bg-blue-600 text-white">
        比較解析
      </button>
      {data && (
        <div className="mt-4">
          <Line data={data} />
        </div>
      )}
    </div>
  );
}
