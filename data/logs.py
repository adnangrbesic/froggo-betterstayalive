from collections import deque

class GameLogger:
    def __init__(self, max_lines=10):
        # deque with appendleft will naturally put newest items at index 0
        self.logs = deque(maxlen=max_lines)

    def log(self, message):
        # No timestamp, just the raw message
        self.logs.appendleft(message)

    def get_logs(self):
        return list(self.logs)