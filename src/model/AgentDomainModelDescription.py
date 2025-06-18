import os
import uuid
from src.model.llm_service import LLMService

class AgentDomainModelDescription:
    """Agent for generating and refining domain model descriptions"""
    
    def __init__(self):
        """Initialize domain model agent with required services"""
        self._connected_agents = {}
        self._llm_service = LLMService()
        self._current_domain_model = None
    
    def connect(self, agent_name, agent_instance):
        """Connect this agent to another agent"""
        self._connected_agents[agent_name] = agent_instance
        print(f"DomainModelAgent connected to {agent_name}")
    
    def send_message(self, to_agent_name, message_type, content):
        """Send a message to another agent"""
        if to_agent_name not in self._connected_agents:
            raise ValueError(f"Agent {to_agent_name} not connected")
            
        message = {
            "from": "DomainModelAgent",
            "type": message_type,
            "content": content
        }
        
        print(f"DomainModelAgent → {to_agent_name}: {message_type}")
        return self._connected_agents[to_agent_name].receive_message(message)
    
    def receive_message(self, message):
        """Receive and process a message from another agent"""
        from_agent = message["from"]
        msg_type = message["type"]
        print(f"{from_agent} → DomainModelAgent: {msg_type}")
        
        if msg_type == "generate_domain_model":
            # Generate domain model based on chat history
            chat_history_text = message["content"].get("chat_history_text", "")
            return self.generate_domain_model(chat_history_text)
            
        elif msg_type == "generate_domain_model_only":
            # Generate only domain model description without requesting visualization
            chat_history_text = message["content"].get("chat_history_text", "")
            return self.generate_domain_model_description_only(chat_history_text)
            
        elif msg_type == "get_domain_model":
            # Return current domain model
            return {"domain_model_description": self._current_domain_model}
            
        elif msg_type == "refine_domain_model":
            # Receive feedback from VisualizationAgent and refine model
            uml_feedback = message["content"].get("uml_feedback", "")
            plant_uml = message["content"].get("plant_uml", "")
            return self.refine_domain_model(uml_feedback, plant_uml)
            
        return {"status": "error", "message": f"Unknown message type: {msg_type}"}
        
    def generate_domain_model(self, chat_history_text):
        """Generate a domain model description from chat history and initiate visualization"""
        try:
            print("DomainModelAgent: Generating domain model from chat history")
            # Use LLM service to generate domain model description
            domain_model_description = self._llm_service.generate_domain_model_description(chat_history_text)
            
            # Store the domain model locally
            self._current_domain_model = domain_model_description
            
            # Notify the chat agent about the new domain model
            if "ChatAgent" in self._connected_agents:
                print("DomainModelAgent: Notifying ChatAgent about new domain model")
                self.send_message(
                    "ChatAgent",
                    "domain_model_updated",
                    {"domain_model_description": domain_model_description}
                )
            
            # Request visualization from visualization agent
            if "VisualizationAgent" in self._connected_agents:
                print("DomainModelAgent: Requesting visualization from VisualizationAgent")
                visualization_result = self.send_message(
                    "VisualizationAgent",
                    "generate_plantuml",
                    {"domain_model_description": domain_model_description}
                )
                
                plant_uml = visualization_result.get("plant_uml", "")
                uml_feedback = visualization_result.get("feedback", "")
                
                # If feedback suggests refinement is needed, refine the model
                if visualization_result.get("needs_refinement", False):
                    print("DomainModelAgent: Visualization agent suggested refinements, updating model")
                    refined_result = self.refine_domain_model(uml_feedback, plant_uml)
                    return {
                        "domain_model_description": refined_result.get("domain_model_description", domain_model_description),
                        "plant_uml": refined_result.get("plant_uml", plant_uml)
                    }
                
                # Return both the domain model and the generated PlantUML
                return {
                    "domain_model_description": domain_model_description,
                    "plant_uml": plant_uml
                }
            
            return {"domain_model_description": domain_model_description}
        except Exception as e:
            print(f"Error generating domain model: {e}")
            return {"error": "Failed to generate domain model description"}
    
    def generate_domain_model_description_only(self, chat_history_text):
        """Generate only the domain model description without requesting visualization"""
        try:
            print("DomainModelAgent: Generating domain model description only (no visualization)")
            # Use LLM service to generate domain model description
            domain_model_description = self._llm_service.generate_domain_model_description(chat_history_text)
            
            # Store the domain model locally
            self._current_domain_model = domain_model_description
            
            # Notify the chat agent about the new domain model
            if "ChatAgent" in self._connected_agents:
                print("DomainModelAgent: Notifying ChatAgent about new domain model description")
                self.send_message(
                    "ChatAgent",
                    "domain_model_updated",
                    {"domain_model_description": domain_model_description}
                )
            
            # Return only the domain model description
            return {"domain_model_description": domain_model_description}
        except Exception as e:
            print(f"Error generating domain model description: {e}")
            return {"error": "Failed to generate domain model description"}
    
    def refine_domain_model(self, uml_feedback, plant_uml):
        """Refine domain model based on visualization feedback"""
        print("DomainModelAgent: Refining domain model based on UML feedback")
        
        # In a production implementation, this would use the feedback to improve the model
        # For now, we'll just acknowledge the refinement request
        
        # If we have feedback, we could use it to enhance the domain model
        if uml_feedback and self._current_domain_model:
            # This would be where the domain model is improved based on visualization feedback
            refined_domain_model = self._current_domain_model
            
            # We would normally update the current model with the refined version
            self._current_domain_model = refined_domain_model
            
            if "ChatAgent" in self._connected_agents:
                self.send_message(
                    "ChatAgent",
                    "domain_model_updated",
                    {"domain_model_description": refined_domain_model}
                )
            
            return {
                "domain_model_description": refined_domain_model,
                "plant_uml": plant_uml
            }
        
        return {"status": "acknowledged", "message": "No refinements made"}
    
    def get_domain_model(self):
        """Get the current domain model description"""
        return {"domain_model_description": self._current_domain_model}
    
    def answer_domain_question(self, question, domain_model):
        """Answer a question about the domain model"""
        try:
            print(f"DomainModelAgent: Answering question about domain model")
            
            if not domain_model:
                return {"answer": "There is no domain model to answer questions about yet. Please create a domain model first."}
            
            prompts = [
                {"role": "system", "content": [{"type": "text", "text": 
                    "You are a domain modeling expert. Your task is to answer questions about an existing domain model. "
                    "Provide clear, concise explanations based on the domain model description provided."
                }]},
                {"role": "user", "content": [{"type": "text", "text": 
                    f"Here is the current domain model description:\n\n{domain_model}\n\n"
                    f"Please answer this question about the domain model: {question}"
                }]}
            ]

            response = self._client.chat.completions.create(
                model=os.getenv("GPT_MODEL"), 
                messages=prompts
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {"answer": answer}
        except Exception as e:
            print(f"Error answering domain question: {e}")
            return {"error": "Failed to answer question about the domain model"}