class Scenario:
    """Data object for storing and managing scenarios."""
    
    def __init__(self, text=None):
        """Initialize a scenario"""
        self.text = text
    
    def set_text(self, text):
        """Set the scenario."""
        self.text = text
    
    def add_text(self, text):
        """Add a new scenario (currently replaces existing one)."""
        self.text = text
    
    def get_text(self):
        """Get the scenario."""
        return self.text