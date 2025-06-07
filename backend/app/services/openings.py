import json
class OpeningBook:
    def __init__(self, path="book.json"):
        with open(path) as f:
            self.book = json.load(f)  # { fen: [ { "move":"e2e4", "weight":10 }, … ] }

    def next_moves(self, fen):
        return self.book.get(fen, [])
