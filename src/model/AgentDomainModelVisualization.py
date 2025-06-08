import os
from src.model.gpt2 import gpt_v2_interface
from src.model.openai_client import OpenAIClient

class AgentDomainModelVisualization:
    """Agent for generating and analyzing PlantUML visualizations from domain models"""
    
    def __init__(self):
        """Initialize visualization agent with required services"""
        self._connected_agents = {}
        self._client = OpenAIClient.get_client()
        self._current_plant_uml = None
    
    def connect(self, agent_name, agent_instance):
        """Connect this agent to another agent"""
        self._connected_agents[agent_name] = agent_instance
        print(f"VisualizationAgent connected to {agent_name}")
    
    def send_message(self, to_agent_name, message_type, content):
        """Send a message to another agent"""
        if to_agent_name not in self._connected_agents:
            raise ValueError(f"Agent {to_agent_name} not connected")
            
        message = {
            "from": "VisualizationAgent",
            "type": message_type,
            "content": content
        }
        
        print(f"VisualizationAgent → {to_agent_name}: {message_type}")
        return self._connected_agents[to_agent_name].receive_message(message)
    
    def receive_message(self, message):
        """Receive and process a message from another agent"""
        from_agent = message["from"]
        msg_type = message["type"]
        print(f"{from_agent} → VisualizationAgent: {msg_type}")
        
        if msg_type == "generate_plantuml":
            # Generate PlantUML from domain model description
            domain_model_description = message["content"].get("domain_model_description", "")
            return self.generate_plantuml(domain_model_description)
            
        elif msg_type == "adjust_plantuml":
            # Adjust existing PlantUML based on user request
            domain_model_description = message["content"].get("domain_model_description", "")
            existing_plant_uml = message["content"].get("existing_plant_uml", "")
            adjustment_request = message["content"].get("adjustment_request", "")
            return self.adjust_plantuml(domain_model_description, existing_plant_uml, adjustment_request)
            
        elif msg_type == "update_domain_model":
            # Generate new visualization when domain model changes
            domain_model_description = message["content"].get("domain_model_description", "")
            return self.generate_plantuml(domain_model_description)
            
        elif msg_type == "get_plantuml":
            # Return current PlantUML
            return {"plant_uml": self._current_plant_uml}
            
        return {"status": "error", "message": f"Unknown message type: {msg_type}"}
    
    def generate_plantuml(self, domain_model_description):
        """Generate PlantUML from domain model description and analyze for quality"""
        if not domain_model_description:
            return {"error": "Domain model description is required"}
        
        try:
            print("VisualizationAgent: Generating PlantUML diagram")
            # Generate PlantUML using GPT-2 interface
            plant_uml = gpt_v2_interface(domain_model_description, self._client)
            
            # Store the generated PlantUML locally
            self._current_plant_uml = plant_uml
            
            # Analyze the quality of the generated UML
            analysis_result = self.analyze_uml_quality(plant_uml, domain_model_description)
            needs_refinement = analysis_result.get("needs_refinement", False)
            feedback = analysis_result.get("feedback", "")
            
            # Notify the domain model agent if refinement is needed
            if needs_refinement and "DomainModelAgent" in self._connected_agents:
                print("VisualizationAgent: UML may need refinement, sending feedback to DomainModelAgent")
                self.send_message(
                    "DomainModelAgent",
                    "refine_domain_model",
                    {
                        "uml_feedback": feedback,
                        "plant_uml": plant_uml
                    }
                )
            
            # Notify the chat agent about the new visualization
            if "ChatAgent" in self._connected_agents:
                print("VisualizationAgent: Notifying ChatAgent about new PlantUML")
                self.send_message(
                    "ChatAgent",
                    "visualization_updated",
                    {"plant_uml": plant_uml}
                )
                
            return {
                "plant_uml": plant_uml,
                "needs_refinement": needs_refinement,
                "feedback": feedback
            }
        except Exception as e:
            print(f"Error generating PlantUML: {e}")
            return {"error": "Failed to generate PlantUML diagram"}
    
    def analyze_uml_quality(self, plant_uml, domain_model_description):
        """Analyze UML quality to provide feedback for potential refinement"""
        # Count number of classes, relationships, and other elements
        lines = plant_uml.split('\n')
        relationship_count = sum(1 for line in lines if ' -- ' in line)
        inheritance_count = sum(1 for line in lines if '<|--' in line)
        aggregation_count = sum(1 for line in lines if 'o--' in line)
        composition_count = sum(1 for line in lines if '*--' in line)
        
        total_relationships = relationship_count + inheritance_count + aggregation_count + composition_count
        
        # Simple analysis - in a real implementation, this would be more sophisticated
        if total_relationships < 2:
            return {
                "needs_refinement": True,
                "feedback": "The UML diagram has very few relationships. Consider enriching the domain model with more connections between entities."
            }
            
        # Check if there are missing attributes or relationships
        if "class" in domain_model_description.lower() and ": " not in plant_uml:
            return {
                "needs_refinement": True,
                "feedback": "Domain model mentions classes with attributes but none appear in the UML diagram."
            }
            
        return {"needs_refinement": False, "feedback": ""}
    
    def get_current_plantuml(self):
        """Get the current PlantUML diagram"""
        return {"plant_uml": self._current_plant_uml}
    
    def adjust_plantuml(self, domain_model_description, existing_plant_uml, adjustment_request):
        """Adjust PlantUML based on user request while preserving the domain model"""
        if not existing_plant_uml:
            # If no existing PlantUML, generate a new one
            return self.generate_plantuml(domain_model_description)
        
        try:
            print("VisualizationAgent: Adjusting PlantUML diagram based on user request")
            
            # Determine what kind of adjustment is needed based on the request
            if "left to right" in adjustment_request.lower():
                # Add or ensure left to right direction
                if "left to right direction" not in existing_plant_uml:
                    lines = existing_plant_uml.split('\n')
                    # Insert after @startuml if it exists
                    if "@startuml" in lines[0]:
                        lines.insert(1, "left to right direction")
                    else:
                        lines.insert(0, "left to right direction")
                    adjusted_plant_uml = "\n".join(lines)
                else:
                    adjusted_plant_uml = existing_plant_uml
            
            elif "top to bottom" in adjustment_request.lower():
                # Remove left to right direction if it exists
                lines = existing_plant_uml.split('\n')
                adjusted_lines = [line for line in lines if "left to right direction" not in line]
                # Add top to bottom direction after @startuml if it exists
                if "@startuml" in adjusted_lines[0]:
                    adjusted_lines.insert(1, "top to bottom direction")
                else:
                    adjusted_lines.insert(0, "top to bottom direction")
                adjusted_plant_uml = "\n".join(adjusted_lines)
            
            else:
                # For more complex adjustments, use the LLM to modify the PlantUML
                prompts = [
                    {"role": "system", "content": [{"type": "text", "text": 
                        "You are a PlantUML expert. Your task is to modify an existing PlantUML diagram based on a user request, "
                        "while preserving all entities and relationships. Do not add or remove any domain elements, only adjust "
                        "the visualization aspects like layout, direction, style, etc."
                    }]},
                    {"role": "user", "content": [{"type": "text", "text": 
                        f"Here is the current PlantUML diagram:\n\n{existing_plant_uml}\n\n"
                        f"Please modify it according to this request: {adjustment_request}\n\n"
                        f"Return only the modified PlantUML code with no explanations."
                    }]}
                ]

                response = self._client.chat.completions.create(
                    model=os.getenv("GPT_MODEL"), 
                    messages=prompts
                )
                
                adjusted_plant_uml = response.choices[0].message.content.strip()
            
            # Store the adjusted PlantUML locally
            self._current_plant_uml = adjusted_plant_uml
            
            # Notify the chat agent about the adjusted visualization
            if "ChatAgent" in self._connected_agents:
                print("VisualizationAgent: Notifying ChatAgent about adjusted PlantUML")
                self.send_message(
                    "ChatAgent",
                    "visualization_updated",
                    {"plant_uml": adjusted_plant_uml}
                )
                
            return {"plant_uml": adjusted_plant_uml}
        
        except Exception as e:
            print(f"Error adjusting PlantUML: {e}")
            # Fall back to the existing PlantUML if any error occurs
            return {"plant_uml": existing_plant_uml, "error": "Failed to adjust PlantUML diagram"}