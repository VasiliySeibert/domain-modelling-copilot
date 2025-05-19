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
        Determine if the input has enough information for domain model description."""
        
        try:
            functions = [
                {
                    "name": "get_decision",
                    "description": "Returns a decision as True or False along with suggestions",
                    "parameters": {
                        "type": "object",
                        "required": ["criteria", "suggestions", "decision"],
                        "properties": {
                            "criteria": {
                                "type": "object",
                                "required": ["condition", "value"],
                                "properties": {
                                    "value": {
                                        "type": "string",
                                        "description": "The value that the condition is compared against."
                                    },
                                    "condition": {
                                        "type": "string",
                                        "description": "Are at least three entities and two relationships provided in the description to allow for a basic domain model?"
                                    }
                                }
                            },
                            "decision": {
                                "type": "boolean",
                                "description": "The decision result, either True or False"
                            },
                            "suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "description": "A suggestion related to the decision"
                                },
                                "description": "When decision=true: List identified entities, relationships, and improvement ideas. When decision=false: List what's missing and questions to ask."
                            }
                        }
                    }
                }
            ]

            prompts = "You are an expert domain modelling engineer according to E. Evans, Domain-driven design: tackling complexity in the heart of software. Addison-Wesley Professional, 2004. You specialized in domain models expressed in UML. Your job is to decide if the user has provided enough information, for a domain model. e.g. if the user just provides his name, information about general things like the weather or just requests some information, then you as an expert don't have enough information to derive a domain model from it. You need some description about a customer domain. You will receive a user input or chat history and your job is to decide if the information in this text is sufficient for creating a domain model. Keep in mind that you talk to a customer, don't be too hard if not all attributes, entities and relationships are provided. To get started you only need at minimum three entities and two relationships. the user cannot be a entity.\n\ne.g. if you are provided with something like \"I own a bicycle store in Hamburg. We sell E bikes and regular bikes.\" then you can already derive a domain model from it. \n\nIf your decision is that you don't have enough information, then please provide information about what else you need for a domain model. Also provide maximum 1 question that the user needs to be asked for a proper domain model. the question must be formulated in a way so that if it was answered, then a domain model can be generated."
            
            # "I will provide you chat history as a single string and you have to use as a context and based on that you have to keep all questions from in mind."
            
            messages = [
                {"role": "system", "content": [{"type": "text", "text": prompts}]},
                {"role": "user", "content": [{"type": "text", "text": chat_history_text}]}
            ]

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
                
                # Ensure result contains suggestions
                if "suggestions" not in result or not result["suggestions"]:
                    if result.get("decision", False):
                        result["suggestions"] = ["Please provide more entities and relationships for the domain model."]
                    else:
                        result["suggestions"] = ["You have provided sufficient information for creating a domain model."]
                
                # Return the result with guaranteed suggestions
                return result
                    
            # Fallback if function call doesn't work as expected
            return {
                "decision": False, 
                "suggestions": ["Consider adding more specific entities and relationships."]
            }
                
        except Exception as e:
            print(f"Error determining input type: {e}")
            # Fallback with default values
            return {
                "decision": False,
                "suggestions": ["Consider adding more specific entities and relationships."]
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