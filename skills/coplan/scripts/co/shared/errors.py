class ExError(Exception):
    pass


class AgentSpawnError(ExError):
    pass


class GateError(ExError):
    def __init__(self, message, data, required_action, next_command=None):
        super().__init__(message)
        self.data = data
        self.required_action = required_action
        self.next_command = next_command
