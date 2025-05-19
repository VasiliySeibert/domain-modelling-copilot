class UMLView {
    constructor() {
        this.elements = {
            // Make sure we're properly selecting the domain model text element
            domainModelText: document.getElementById('domainModelText'),
            domainModelLoading: document.getElementById('domainModelLoading'),
            plantumlText: document.getElementById('plantumlText'),
            plantumlLoading: document.getElementById('plantumlLoading'),
            generateUMLBtn: document.getElementById('generateUMLBtn')
        };

        // Add validation to ensure all elements were found
        this.validateElements();
    }

    // Add this method to check that all elements exist
    validateElements() {
        const missingElements = [];
        
        // Check each element and collect any that are missing
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                missingElements.push(key);
            }
        }
    }

    // Update the setDomainModelDescription method to check for the element's existence
    setDomainModelDescription(domainModelDescription) {
        if (!this.elements.domainModelText) {
            console.error("domainModelText element not found in the DOM");
            return; // Exit the function early if the element doesn't exist
        }
        
        this.elements.domainModelText.textContent = domainModelDescription || "No detailed description provided.";
        
        if (domainModelDescription && domainModelDescription.trim()) {
            this.generateUMLFromDomainModelDescription(domainModelDescription);
        }
        
        // Always dispatch event that domain model was updated
        document.dispatchEvent(new CustomEvent('domainModelUpdated'));
    }
    
    // Similar checks should be added to other methods that access DOM elements
    generateUMLFromDomainModelDescription(domainModelDescriptionText) {
        if (!this.elements.plantumlText) {
            console.error("plantumlText element not found in the DOM");
            return;
        }
        
        // Show loading state
        this.elements.plantumlText.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        
        fetch("/generate_uml", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ domainModelDescriptionText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                this.elements.plantumlText.textContent = "Error generating UML: " + data.error;
            } else if (data.plantuml) {
                this.setPlantUML(data.plantuml);
            } else {
                this.elements.plantumlText.textContent = "No UML diagram could be generated from the provided domain model description.";
            }
        })
        .catch(err => {
            console.error("Error generating UML:", err);
            this.elements.plantumlText.textContent = "Failed to generate UML diagram. Please try again.";
        });
    }

    displayDefaultPlantUML() {
        const staticUML = `@startuml
' Domain Model Example
package "Business Domain" {
    class Entity {
        +id: String
        +name: String
        +createdAt: DateTime
        +updatedAt: DateTime
    }
    
    class BusinessEntity extends Entity {
        +taxId: String
        +registrationNumber: String
        +validate(): Boolean
    }
    
    class Person extends Entity {
        +email: String
        +phone: String
        +dateOfBirth: Date
        +getAge(): Integer
    }
    
    class Relationship {
        +startDate: Date
        +endDate: Date
        +status: String
        +isActive(): Boolean
    }
    
    BusinessEntity "1" -- "0..*" Person: employs >
    Person "1" -- "0..*" Relationship: participates in >
}
@enduml`;
        
        this.elements.plantumlText.textContent = staticUML;
    }
    
    bindGenerateUML() {
        // Will be triggered when setScenario is called
    }
    
    setScenario(scenario) {
        this.elements.scenarioText.textContent = scenario || "No detailed description provided.";
        
        if (scenario && scenario.trim()) {
            this.generateUMLFromScenario(scenario);
        }
    }
    
    generateUMLFromScenario(scenarioText) {
        // Show loading state
        this.elements.plantumlText.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        
        fetch("/generate_uml", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenarioText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                this.elements.plantumlText.textContent = "Error generating UML: " + data.error;
            } else if (data.plantuml) {
                this.setPlantUML(data.plantuml);
            } else {
                this.elements.plantumlText.textContent = "No UML diagram could be generated from the provided scenario.";
            }
        })
        .catch(err => {
            console.error("Error generating UML:", err);
            this.elements.plantumlText.textContent = "Failed to generate UML diagram. Please try again.";
        });
    }
    
    setPlantUML(plantUML) {
        if (!this.elements.plantumlText) {
            console.error("plantumlText element not found in the DOM");
            return;
        }
        
        this.elements.plantumlText.textContent = plantUML;
        
        // Render the PlantUML diagram
        this.renderPlantUMLDiagram(plantUML);
        
        // Dispatch event that UML was updated
        document.dispatchEvent(new CustomEvent('umlUpdated'));
    }
    
    getScenarioText() {
        return this.elements.scenarioText.textContent.trim();
    }
    
    getPlantUMLText() {
        return this.elements.plantumlText.textContent.trim();
    }
    
    getDomainModelDescriptionText() {
        return this.elements.domainModelText.textContent.trim();
    }

    // Add this method to the UMLView class
    renderPlantUMLDiagram(plantUML) {
        if (!plantUML || !plantUML.trim()) {
            // No PlantUML code to render
            return;
        }
        
        try {
            // Encode the PlantUML text for use with the PlantUML server
            const encodedUML = this.encodePlantUML(plantUML);
            const imageUrl = `https://www.plantuml.com/plantuml/img/${encodedUML}`;
            
            // Find elements
            const umlImage = document.getElementById('umlImage');
            const umlPlaceholder = document.getElementById('umlPlaceholder');
            
            if (umlImage && umlPlaceholder) {
                // Set the image source
                umlImage.src = imageUrl;
                umlImage.classList.remove('d-none');
                umlPlaceholder.classList.add('d-none');
                
                // Add loading and error handlers
                umlImage.onload = () => {
                    console.log("PlantUML diagram loaded successfully");
                };
                
                umlImage.onerror = () => {
                    console.error("Error loading PlantUML diagram");
                    umlImage.classList.add('d-none');
                    umlPlaceholder.classList.remove('d-none');
                    umlPlaceholder.innerHTML = `
                        <i class="bi bi-exclamation-triangle fs-1 opacity-50 text-warning"></i>
                        <p class="mt-2">Error rendering diagram. Please check your PlantUML syntax.</p>
                    `;
                };
            }
        } catch (error) {
            console.error("Error rendering PlantUML diagram:", error);
        }
    }

    // Add PlantUML encoding method
    encodePlantUML(plantUML) {
        // PlantUML text encoding function
        return btoa(unescape(encodeURIComponent(plantUML)))
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
    }
}