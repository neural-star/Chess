import time
from threading import Lock

class ChessClock:
    def __init__(self, base_sec: int, increment_sec: int):
        self.times = {"white": base_sec, "black": base_sec}
        self.inc   = increment_sec
        self.lock  = Lock()
        self.last_timestamp = time.time()
        self.current = "white"

    def switch(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_timestamp
            self.times[self.current] -= elapsed
            self.times[self.current] += self.inc
            self.current = "black" if self.current=="white" else "white"
            self.last_timestamp = now

    def get_times(self):
        with self.lock:
            # 更新中の残り時間を計算して返す
            now = time.time()
            rem = self.times[self.current] - (now - self.last_timestamp)
            return {
                "white": int(self.times["white"]),
                "black": int(self.times["black"]),
                self.current: int(rem)
            }
