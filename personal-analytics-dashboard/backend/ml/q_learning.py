class QAgent:
    def __init__(self):
        self.q_table = {}  # state -> action -> value

    def choose_action(self, state):
        # Placeholder: always no change
        return "NO_CHANGE"

    def update(self, state, action, reward, next_state):
        # Placeholder: do nothing until training added
        pass
