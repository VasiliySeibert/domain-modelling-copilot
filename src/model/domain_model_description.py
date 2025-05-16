class DomainModelDescription:
    """Data object for storing and managing domain model descriptions."""
    
    def __init__(self, text=None):
        """Initialize a domain model description"""
        self.text = text
    
    def set_text(self, text):
        """Set the domain model description."""
        self.text = text
    
    def add_text(self, text):
        """Add a new domain model description (currently replaces existing one)."""
        self.text = text
    
    def get_text(self):
        """Get the domain model description."""
        return self.text