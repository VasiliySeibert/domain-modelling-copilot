from openai_client import OpenAIClient
import os

class LLMWrapper:
    """Wrapper for language model functionality."""
    
    def __init__(self):
        """Initialize the LLM wrapper with an empty chat history."""
        self.chat_history = []
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
            ] + self.chat_history

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            bot_reply = response.choices[0].message.content.strip()
            self.chat_history.append({"role": "assistant", "content": bot_reply})
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
                        "You are a domain modeling copilot. Your task is to generate clear and structured natural language descriptions of domain models based on user input."
                        "You describe entities, their relationships, and their components in a professional and informative way, similar to product or business documentation."
                        "Use the following style as a reference:"
                        "In our action camera store, we specialize in cameras designed for adventurers and professionals seeking rugged and versatile solutions to capture their journeys. The inclusion of different models like ActionCamPro and AdventureCamX caters to a comprehensive range of activities and environments..."
                        "Use this style to generate similar descriptions for other domains based on user input."
                    )
                },
                {"role": "user", "content": f"Generate a clear and structured scenario for the following input:\n\n{scenario_text}"}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating scenario: {e}")
            return "An error occurred while generating the scenario."
    
    def generate_summary(self, detailed_description):
        """Generate a summary from the given detailed scenario."""
        try:
            prompts = [
                {"role": "system", "content": 
                    "Summarize the following scenario in one sentence."
                    "At last ask something in next line. For example, 'Is there anything else I can help you with?'"
                },
                {"role": "user", "content": f"Summarize the following scenario:\n\n{detailed_description}"}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            summary = response.choices[0].message.content.strip()
            self.chat_history.append({"role": "assistant", "content": summary})
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "An error occurred while generating the summary."
    
    def add_to_chat_history(self, role, content):
        """Add an entry to the chat history."""
        self.chat_history.append({"role": role, "content": content})
    
    def get_chat_history(self):
        """Get the current chat history."""
        return self.chat_history
    
    def clear_chat_history(self):
        """Clear the chat history."""
        self.chat_history = []