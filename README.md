# ♟️ Chess AI App (with Gradio + Stockfish)

AIチェス対戦を楽しめるWebアプリです。  
人間 vs AI、AI vs AI、ヒント機能などを備え、初心者から上級者までプレイ可能！

このアプリは [Gradio](https://www.gradio.app/) をベースに構築され、[Stockfish](https://stockfishchess.org/) エンジンを使用しています。

---

## 🚀 主な機能

- ✅ 人間 vs AI（手入力でプレイ）
- 🔁 AI vs AI（スキル別に1手ずつ進行）
- 🧠 駒の移動候補（ヒント）を表示
- 🔄 ゲームのリセット
- 🧑‍🤝‍🧑 フレンド招待対戦（今後追加）
- 📊 指し手の評価グラフ（今後追加）

---

## 🐳 Docker での起動手順

> ⚠️ Docker は事前にインストールしてください。  
> Ubuntu では `sudo apt install docker.io`  
> Windos/macOS では [Docker Desktop](https://www.docker.com/products/docker-desktop/) を使用

### 1. リポジトリをクローン

```bash
git clone https://github.com/neural-star/chess.git
cd chess
```

### 2. Docker イメージをビルド

```bash
docker build -t chess .
```

### 3. Docker コンテナを起動

```bash
docker run -p 7860:7860 chess
```

### 4. アクセス

起動後、以下のURLにアクセスしてチェスをプレイできます：
http://localhost:7860

### 📁 フォルダ構成

```bash
chess/
├── app.py
├── puzzle.py
├── puzzle.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```
