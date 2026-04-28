# Simple in-memory (for demo)
# Later you can replace with Redis

class Memory:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def update(self, key, value_dict):
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(value_dict)


# Global memory instance
memory = Memory()