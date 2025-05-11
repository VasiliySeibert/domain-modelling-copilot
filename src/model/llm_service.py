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
    
    def determine_input_type(self, user_input):
        """Determine if the input has enough information for domain modeling."""
        try:
            # Using OpenAI function calling to get a more detailed analysis
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
                                        "description": "The input text being evaluated"
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
            Your job is to decide if the user has provided enough information for a domain model.
            
            Guidelines:
            - You need at minimum three entities and two relationships
            - The user themselves cannot be an entity
            - If provided with something like "I own a bicycle store in Hamburg. We sell E bikes and regular bikes," 
              this contains enough information (Store, E-bike, Regular bike entities)
            
            Use the function to return your analysis with a boolean decision and suggestions."""

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
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

            print(json.dumps(function_call_dict, indent=2))
            
            if function_call and function_call.name == "get_decision":
                result = json.loads(function_call.arguments)
                
                # Store the full analysis for potential later use
                self._last_analysis = result
                
                # Return "scenario" if there's enough info, otherwise "general"
                return "scenario" if result.get("decision") else "general"
                
            # Fallback if function call doesn't work as expected
            return "general"
                
        except Exception as e:
            print(f"Error determining input type: {e}")
            # Fallback to simpler classification if function calling fails
            try:
                prompts = [
                    {"role": "system", "content": "Classify the input as either 'general' or 'scenario'."},
                    {"role": "user", "content": f"Input: {user_input}"}
                ]

                response = self.client.chat.completions.create(
                    model=os.getenv("GPT_MODEL"), messages=prompts
                )
                return response.choices[0].message.content.strip().lower()
            except Exception as e2:
                print(f"Fallback classification also failed: {e2}")
                return "general"  # Default to "general" in case of an error
                
    # Add helper method to get the last analysis (optional enhancement)
    def get_last_analysis(self):
        """Get the detailed analysis from the last input classification."""
        return getattr(self, "_last_analysis", None)
    
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