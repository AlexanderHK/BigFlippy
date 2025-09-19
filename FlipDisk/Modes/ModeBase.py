class ModeBase:
    def run(self, *args, **kwargs):
        raise NotImplementedError("Run method must be implemented by subclass.")

    def shutdown(self):
        pass  # Implement shutdown logic if needed

    def receive_data(self, data):
        pass  # Placeholder for future implementation
