from Modes.ModeBase import ModeBase

class StandbyMode(ModeBase):
    def __init__(self):
        self.state = "STANDBY"

    def run(self, *args, **kwargs):
        print("Waiting for next mode change")
        # Add standby logic here

    def shutdown(self):
        self.state = "STOPPED"

    def receive_data(self, data):
        pass
