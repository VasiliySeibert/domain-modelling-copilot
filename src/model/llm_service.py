from src.model.openai_client import OpenAIClient
from src.model.chat_history import ChatHistory
from src.model.scenario import Scenario
import os
import json

class LLMService:
    """Service for language model operations."""
    
    def __init__(self):
        """Initialize the LLM service with chat history and scenario objects."""
        self.chat_history = ChatHistory()
        self.current_scenario = Scenario()
        self.client = OpenAIClient.get_client()
    
    def determine_input_type(self, chat_history):
        """
        Determine if the input has enough information for domain model description."""
        try:
            functions = [
                {
                    "name": "get_decision",
                    "description": "Returns a decision about domain modeling potential with suggestions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "criteria": {
                                "type": "object",
                                "properties": {
                                    "value": {
                                        "type": "string",
                                        "description": "The chat history being evaluated"
                                    },
                                    "condition": {
                                        "type": "string",
                                        "description": "The condition for domain modeling potential"
                                    }
                                },
                                "required": ["condition", "value"]
                            },
                            "decision": {
                                "type": "boolean",
                                "description": "True if there's enough information for domain modeling, false otherwise"
                            },
                            "suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Suggestions for improving domain model information"
                            }
                        },
                        "required": ["criteria", "decision", "suggestions"]
                    }
                }
            ]

            system_prompt = """You are an expert domain modelling engineer according to E. Evans, Domain-driven design principles. 
            Your job is to decide if the chat history has enough information for a domain model.
            
            Guidelines:
            - You need at minimum three entities and two relationships
            - The user themselves cannot be an entity
            - If provided with something like "I own a bicycle store in Hamburg. We sell E bikes and regular bikes," 
              this contains enough information (Store, E-bike, Regular bike entities)
            Analyze the ENTIRE chat history, not just the last message.
            Use the function to return your analysis with a boolean decision and suggestions."""

            # Create messages array with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history messages directly as an array
            messages.extend(chat_history)

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"),
                messages=messages,
                functions=functions,
                function_call={"name": "get_decision"}
            )
            
            # Extract function call result
            function_call = response.choices[0].message.function_call

            # Print in JSON format
            function_call_dict = {
                "name": function_call.name,
                "arguments": json.loads(function_call.arguments) if hasattr(function_call, "arguments") else None
            }

            # Print the function call details
            print(json.dumps(function_call_dict, indent=2))
            
            if function_call and function_call.name == "get_decision":
                result = json.loads(function_call.arguments)
                
                # Return the result directly
                return result
                    
            # Fallback if function call doesn't work as expected
            return {
                "decision": False, 
                "suggestions": ["Consider adding more specific entities and relationships"]
            }
                
        except Exception as e:
            print(f"Error determining input type: {e}")
            # Fallback with default values
            return {
                "decision": False,
                "suggestions": ["Consider adding more specific entities and relationships"]
            }

    # Generate a domain model description based on user input
    def generate_scenario(self, scenario_text):
        """Generate a detailed scenario from the given user input."""
        try:
            prompts = [
                {
                    "role": "system",
                    "content": (
                        "You are a domain modeling copilot. Generate clear, structured natural language descriptions of domain models. Focus on classes, attributes, and relationships. Be concise and specific. "
                        "Avoid lengthy narratives or stories. Format your response as a professional business analysis document with appropriate sections for key entities and their relationships."
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
    
    # Add helper methods to manage chat history
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