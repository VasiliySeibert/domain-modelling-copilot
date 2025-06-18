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
        Determine if the input has enough information for domain model description or if it's an update to an existing one.
        Also detects style change requests and irrelevant/casual messages.
        """
        
        try:
            functions = [
                {
                    "name": "get_decision",
                    "description": "Returns a decision about domain model generation and appropriate response",
                    "parameters": {
                        "type": "object",
                        "required": ["decision", "is_update", "is_casual_comment", "is_style_change", "suggestions"],
                        "properties": {
                            "decision": {
                                "type": "boolean",
                                "description": "True if there's enough information for a domain model, False otherwise"
                            },
                            "is_update": {
                                "type": "boolean", 
                                "description": "True if this is an update to an existing domain model rather than a first request"
                            },
                            "is_casual_comment": {
                                "type": "boolean",
                                "description": "True if this is just a casual comment (like 'wow', 'nice') that doesn't require updating the domain model"
                            },
                            "is_style_change": {
                                "type": "boolean",
                                "description": "True if the user is requesting to change the style/formatting of the description without changing the domain content"
                            },
                            "style_type": {
                                "type": "string",
                                "description": "If is_style_change is true, specifies the requested style (e.g., 'shorter', 'technical', 'software_engineer')"
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

YOUR TASK: Analyze chat history to determine if a domain model can be generated, updated, if the message is a style change request, or if it's unrelated to domain modeling.

MESSAGE CLASSIFICATION:
1. INITIAL DOMAIN MODEL REQUEST: When user first describes multiple entities (3+) and relationships (2+) in their domain.
   - Example: "I want to open a store with products, customers, and employees. Customers buy products and employees sell them."

2. DOMAIN MODEL UPDATE: When user adds new entities or relationships to an existing model.
   - Example: "Now I also want to add suppliers who provide products to the store."
   - Look for phrases like "add", "also", "now include", "additionally"

3. STYLE CHANGE REQUEST: User wants to change how the description is written, not the content.
   - Examples: "make the description shorter", "can you write it from a software engineer's perspective", "simplify the description"
   - For these, identify the specific style requested (shorter, technical, software_engineer, etc.)

4. CASUAL COMMENT: Brief reactions that don't add domain information.
   - Examples: "wow", "nice", "thank you", "looks good", "great", "awesome", "perfect"
   - IMPORTANT: If a domain model exists and user sends ONLY praise/acknowledgment, classify as CASUAL

5. QUESTION/CLARIFICATION: User asks about the domain model without adding new information.
   - Example: "What does this relationship mean?" or "Can you explain this part?"

6. OFF-TOPIC: Message unrelated to domain modeling.
   - Example: "What's the weather today?"

HOW TO DETERMINE IF A DOMAIN MODEL EXISTS:
- Look for previous bot messages containing detailed entity descriptions
- Look for phrases like "Here's the domain model" or "I've updated the domain model"

RESPONSE GUIDELINES:
- For STYLE CHANGE REQUESTS: Acknowledge the style change request.
  "I've reformatted the domain model description as requested."
  "I've made the description more technical as requested."

- For CASUAL COMMENTS: Acknowledge without regenerating model. Use varied responses like:
  "Glad you like it! Let me know if you want to add more entities or relationships."
  "Thanks! I'm here if you need to make any changes to the model."

- For DOMAIN MODEL UPDATES: Acknowledge changes and provide extension suggestions.
  
- For INITIAL REQUESTS: Neutral response with helpful suggestions.

IMPORTANT: Response should be in bullet points(3 max).
"""
        
            messages = [
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "text", "text": chat_history_text}]}
            ]

            response = self.client.chat.completions.create(
                model=os.getenv("GPT_MODEL"),
                messages=messages,
                functions=functions,
                function_call={"name": "get_decision"}
            )
            
            function_call = response.choices[0].message.function_call
            
            if function_call and function_call.name == "get_decision":
                result = json.loads(function_call.arguments)
                
                # Ensure all required fields are present with sensible defaults
                if "is_style_change" not in result:
                    result["is_style_change"] = False
                    
                if "style_type" not in result and result.get("is_style_change", False):
                    result["style_type"] = "general"
                    
                if "suggestions" not in result or not result["suggestions"]:
                    if result.get("is_style_change", False):
                        result["suggestions"] = ["I've reformatted the domain model description as requested."]
                    elif result.get("is_casual_comment", False):
                        result["suggestions"] = ["I'm glad you like it! Let me know if you want to make any changes to the domain model."]
                    elif result.get("is_update", False):
                        result["suggestions"] = ["I've updated the domain model with your changes."]
                    elif result.get("decision", False):
                        result["suggestions"] = ["I've created a domain model based on your description."]
                    else:
                        result["suggestions"] = ["Please provide more details about the entities and relationships in your domain."]
                
                return result
                    
            # Fallback if function call doesn't work as expected
            return {
                "decision": False, 
                "is_update": False,
                "is_casual_comment": False,
                "is_style_change": False,
                "suggestions": ["I need more information about your domain to help you. Could you describe the main entities and how they relate to each other?"]
            }
                
        except Exception as e:
            print(f"Error determining input type: {e}")
            # Fallback with default values
            return {
                "decision": False,
                "is_update": False,
                "is_casual_comment": False,
                "is_style_change": False,
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
                        "IMPORTANT: Only describe entities and relationships explicitly mentioned by the user. Do not add any additional entities, relationships, or functionalities that were not explicitly stated. Stick strictly to what the user has described. Focus on clarifying the existing entities and relationships without elaboration beyond the user's input."
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