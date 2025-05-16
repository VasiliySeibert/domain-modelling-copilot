class ChatHistory:
    """Data object for storing and managing chat history."""
    
    def __init__(self):
        """Initialize an empty chat history."""
        self.chat_history = []
    
    def add_message(self, role, content):
        """Add a message to the chat history."""
        self.chat_history.append({"role": role, "content": content})
    
    def get_messages(self):
        """Get all messages in the chat history."""
        return self.chat_history
    
    def clear(self):
        """Clear all messages from the chat history."""
        self.chat_history = []