from src.model.openai_client import OpenAIClient
from src.model.chat_history import ChatHistory
from src.model.domain_model_description import DomainModelDescription
import os
import json

class LLMService:
    """Service for language model operations."""
    
    def __init__(self):
        """Initialize the LLM service with chat history and domain model description objects."""
        self.chat_history = ChatHistory()
        self.current_domain_model_description = DomainModelDescription()
        self.client = OpenAIClient.get_client()
    
    def determine_input_type(self, chat_history_text):
        """
        Determine what the user is requesting and which agent should handle it.
        Classifies input to determine exactly what functionality is needed.
        """
    
        try:
            functions = [
                {
                    "name": "classify_request",
                    "description": "Classifies the user's request to determine appropriate handling",
                    "parameters": {
                        "type": "object",
                        "required": [
                            "request_type", 
                            "requires_domain_model_update",
                            "requires_plantuml_update", 
                            "description_only_update",
                            "casual_comment",
                            "suggestions"
                        ],
                        "properties": {
                            "request_type": {
                                "type": "string",
                                "enum": [
                                    "INITIAL_DOMAIN_MODEL", 
                                    "UPDATE_DOMAIN_MODEL",
                                    "UPDATE_DESCRIPTION_ONLY", 
                                    "DOMAIN_MODEL_QUESTION", 
                                    "PLANTUML_ADJUSTMENT",
                                    "CASUAL_COMMENT",
                                    "OFF_TOPIC"
                                ],
                                "description": "The type of request being made by the user"
                            },
                            "requires_domain_model_update": {
                                "type": "boolean",
                                "description": "Whether this request requires creating or updating the domain model"
                            },
                            "requires_plantuml_update": {
                                "type": "boolean",
                                "description": "Whether this request requires creating or updating the PlantUML visualization"
                            },
                            "description_only_update": {
                                "type": "boolean",
                                "description": "Whether the user is explicitly requesting to update ONLY the domain model description text without changing the diagram"
                            },
                            "casual_comment": {
                                "type": "boolean",
                                "description": "Whether this is just a casual comment or acknowledgment"
                            },
                            "suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "description": "A suggestion or response line"
                                },
                                "description": "Array of strings that form the complete response to show the user"
                            }
                        }
                    }
                }
            ]

            system_prompt = """You are an expert domain modeling engineer specialized in UML and domain-driven design.

YOUR TASK: Analyze the user's request to determine exactly what they want you to do.

REQUEST CLASSIFICATION TYPES:
1. INITIAL_DOMAIN_MODEL: When user first describes their domain and needs a complete domain model created
   - Example: "I want to open a store with products, customers, and employees. Customers buy products and employees sell them."

2. UPDATE_DOMAIN_MODEL: When user wants to add/modify entities or relationships in an existing domain model
   - Example: "Now I also want to add suppliers who provide products to the store."
   - Look for phrases like "add", "also", "now include", "additionally"

3. UPDATE_DESCRIPTION_ONLY: User wants to update only the textual description without changing the UML diagram
   - Examples: "Can you update just the domain description to be more formal?", "Keep the diagram but make the text clearer"
   - Look for phrases like "just the description", "only the text", "update the description but keep the diagram"

4. DOMAIN_MODEL_QUESTION: User is asking questions about the domain model without necessarily changing it
   - Example: "What does this relationship mean?" or "Can you explain this part of the model?"

5. PLANTUML_ADJUSTMENT: User wants specific changes to the PlantUML diagram without major domain model changes
   - Example: "Can you make the diagram display left to right instead of top to bottom?"

6. CASUAL_COMMENT: Brief reactions that don't add domain information or request changes
   - Examples: "wow", "nice", "thank you", "looks good", "great", "awesome", "perfect"

7. OFF_TOPIC: Message unrelated to domain modeling or the current project
   - Example: "What's the weather today?"

RESPONSE FORMAT:
- Analyze the request thoroughly to determine what the user is trying to achieve
- Set appropriate boolean flags for each action needed
- Provide helpful suggestions in response to the user's request

ADDITIONAL RULES:
- Assume an UPDATE_DOMAIN_MODEL requires both domain model and PlantUML updates
- UPDATE_DESCRIPTION_ONLY should keep the existing PlantUML diagram unchanged
- PLANTUML_ADJUSTMENT should focus on visualization changes without changing the domain model content
"""
        
            messages = [
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "text", "text": chat_history_text}]}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"),
                messages=messages,
                functions=functions,
                function_call={"name": "classify_request"}
            )
            
            function_call = response.choices[0].message.function_call
            
            if function_call and function_call.name == "classify_request":
                result = json.loads(function_call.arguments)
                
                # Ensure default values are set for backwards compatibility
                result["decision"] = result.get("requires_domain_model_update", False)
                result["is_update"] = result.get("request_type") == "UPDATE_DOMAIN_MODEL"
                result["is_casual_comment"] = result.get("casual_comment", False)
                result["update_description_only"] = result.get("description_only_update", False)
                
                # Generate default suggestions if none provided
                if "suggestions" not in result or not result["suggestions"]:
                    request_type = result.get("request_type")
                    if request_type == "INITIAL_DOMAIN_MODEL":
                        result["suggestions"] = ["I'll create a domain model based on your description."]
                    elif request_type == "UPDATE_DOMAIN_MODEL":
                        result["suggestions"] = ["I'll update the domain model with your changes."]
                    elif request_type == "UPDATE_DESCRIPTION_ONLY":
                        result["suggestions"] = ["I'll update the domain model description while keeping the existing diagram unchanged."]
                    elif request_type == "DOMAIN_MODEL_QUESTION":
                        result["suggestions"] = ["Let me explain that aspect of the domain model for you."]
                    elif request_type == "PLANTUML_ADJUSTMENT":
                        result["suggestions"] = ["I'll adjust the visualization as requested."]
                    elif request_type == "CASUAL_COMMENT":
                        result["suggestions"] = ["Glad you like it! Let me know if you want to make any changes to the model."]
                    else:
                        result["suggestions"] = ["Could you tell me more about your domain model needs?"]
            
                return result
                
            # Fallback if function call doesn't work as expected
            return {
                "request_type": "OFF_TOPIC",
                "requires_domain_model_update": False,
                "requires_plantuml_update": False, 
                "description_only_update": False,
                "casual_comment": False,
                "decision": False,
                "is_update": False,
                "is_casual_comment": False,
                "update_description_only": False,
                "suggestions": ["I need more information about your domain to help you. Could you describe the main entities and how they relate to each other?"]
            }
            
        except Exception as e:
            print(f"Error determining input type: {e}")
            # Fallback with default values
            return {
                "request_type": "OFF_TOPIC",
                "requires_domain_model_update": False,
                "requires_plantuml_update": False,
                "description_only_update": False,
                "casual_comment": False,
                "decision": False,
                "is_update": False,
                "is_casual_comment": False, 
                "update_description_only": False,
                "suggestions": ["I encountered an issue while analyzing your input. Could you try describing your domain again with key entities and relationships?"]
            }

    def generate_domain_model_description(self, chat_history_text):
        """Generate a structured domain model description from the given chat history."""
        try:
            prompts = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": 
                        "You are a domain modeling expert. Your task is to generate a structured, precise description of a domain model in clear, natural language."
                        "\n\nExample format: 'The following domain model describes the entities Salesperson, RepairPerson, Customer, and Bike. Salesperson, RepairPerson, and Customer are connected to the entity Bike through associations. The Salesperson is associated with the Bike entity with the description 'sells' and 1 Salesperson can sell many Bikes. The RepairPerson is associated with the Bike entity with the description 'repairs' and 1 RepairPerson can repair many Bikes. The Customer is associated with the Bike entity with the description 'buys' and 1 Customer can buy many Bikes."
                        """
                        STRICT EXTRACTION RULES:
1. ONLY include entities explicitly named by the user
2. ONLY include attributes explicitly mentioned for these entities
3. ONLY include relationships clearly described between these entities
4. DO NOT introduce new entities or concepts
5. DO NOT infer additional attributes
6. DO NOT assume relationships that weren't stated
7. DO NOT add any functionality or behavior not explicitly mentioned
8. If something is ambiguous, DO NOT guess or assume - omit it entirely
"""
                    }]
                },
                {"role": "user", "content": [{"type": "text", "text": f"Generate a domain model description for the following conversation: \n\n{chat_history_text}"}]}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), messages=prompts
            )
            generated_domain_model_description = response.choices[0].message.content.strip()
            self.current_domain_model_description.set_text(generated_domain_model_description)
            return generated_domain_model_description
        except Exception as e:
            print(f"Error generating domain model description: {e}")
            return "An error occurred while generating the domain model description."
    
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
        
    def get_current_domain_model_description(self):
        """Get the current domain model description."""
        return self.current_domain_model_description.get_text()