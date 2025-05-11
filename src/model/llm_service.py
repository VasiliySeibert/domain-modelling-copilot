from src.model.openai_client import OpenAIClient
from src.model.chat_history import ChatHistory
from src.model.scenario import Scenario
import os

class LLMService:
    """Service for language model operations."""
    
    def __init__(self):
        """Initialize the LLM service with chat history and scenario objects."""
        self.chat_history = ChatHistory()
        self.current_scenario = Scenario()
        self.client = OpenAIClient.get_client()
    
    def determine_input_type(self, user_input):
        """Determine if the input is general or scenario type."""
        try:
            prompts = [
                {"role": "system", "content": "Classify the input as either 'general_type' or 'scenario_type'."},
                {"role": "user", "content": f"Input: {user_input}"}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            return response.choices[0].message.content.strip().lower()
        except Exception as e:
            print(f"Error determining input type: {e}")
            return "general_type"  # Default to "general_type" in case of an error
    
    def generate_response(self, user_name):
        """Generate a general response using GPT."""
        try:
            prompts = [
                {"role": "system", "content": f"You are a helpful assistant. The user's name is {user_name}."}
            ] + self.chat_history.get_messages()

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            bot_reply = response.choices[0].message.content.strip()
            self.chat_history.add_message("assistant", bot_reply)
            return bot_reply
        except Exception as e:
            print(f"Error generating response: {e}")
            return "An error occurred while processing your request."
    
    def generate_scenario(self, scenario_text):
        """Generate a detailed scenario from the given user input."""
        try:
            prompts = [
                {
                    "role": "system",
                    "content": (
                        "You are a domain modeling copilot. Generate clear, structured natural language descriptions "
                        "of domain models. Focus on classes, attributes, and relationships. Be concise and specific. "
                        "Avoid lengthy narratives or stories. Format your response as a professional business analysis "
                        "document with appropriate sections for key entities and their relationships."
                    )
                },
                {"role": "user", "content": f"Generate a domain model description for: {scenario_text}"}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            generated_scenario = response.choices[0].message.content.strip()
            self.current_scenario.set_text(generated_scenario)
            return generated_scenario
        except Exception as e:
            print(f"Error generating scenario: {e}")
            return "An error occurred while generating the scenario."
    
    def generate_summary(self, detailed_description):
        """Generate a summary from the given detailed scenario."""
        try:
            prompts = [
                {"role": "system", "content": 
                    "Summarize the following scenario in one sentence. "
                    "On a new line, ask if the user would like to refine any aspects of the model."
                },
                {"role": "user", "content": f"Summarize the following domain model:\n\n{detailed_description}"}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            summary = response.choices[0].message.content.strip()
            self.chat_history.add_message("assistant", summary)
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "An error occurred while generating the summary."
    
    def add_to_chat_history(self, role, content):
        """Add an entry to the chat history."""
        self.chat_history.add_message(role, content)
    
    def get_chat_history(self):
        """Get the current chat history."""
        return self.chat_history.get_messages()
    
    def clear_chat_history(self):
        """Clear the chat history."""
        self.chat_history.clear()
        
    def get_current_scenario(self):
        """Get the current scenario."""
        return self.current_scenario.get_text()