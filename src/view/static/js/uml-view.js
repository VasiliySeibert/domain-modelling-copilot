class UMLView {
    constructor() {
        this.elements = {
            domainModelText: document.getElementById('domainModelText'),
            domainModelLoading: document.getElementById('domainModelLoading'),
            plantumlText: document.getElementById('plantumlText'),
            plantumlLoading: document.getElementById('plantumlLoading'),
            generateUMLBtn: document.getElementById('generateUMLBtn'),
            // Add the new loading indicator element
            umlLoadingIndicator: document.getElementById('umlLoadingIndicator')
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

    // Update the setDomainModelDescription method to preserve initial welcome text
    setDomainModelDescription(domainModelDescription, generateUml = true) {
        if (!this.elements.domainModelText) {
            console.error("domainModelText element not found in the DOM");
            return; // Exit the function early if the element doesn't exist
        }
        
        const currentText = this.elements.domainModelText.textContent;
        const isInitialText = currentText.includes("Welcome to your new project!");
        
        // Don't update if domain model description is empty/undefined and we have the initial welcome text
        if ((domainModelDescription === undefined || domainModelDescription === '') && isInitialText) {
            console.log("Preserving initial welcome text");
            return;
        }
        
        // Apply fade-in animation to domain model text
        this.elements.domainModelText.style.opacity = "0";
        
        // Only replace text if we have a meaningful domain model description
        if (domainModelDescription && domainModelDescription.trim()) {
            this.elements.domainModelText.textContent = domainModelDescription;
        } else if (!isInitialText) {
            // Only change to "No detailed description" if it's not already the welcome text
            this.elements.domainModelText.textContent = "No detailed description provided.";
        }
        
        // Trigger reflow to restart animation
        void this.elements.domainModelText.offsetWidth;
        
        // Apply fade-in
        this.elements.domainModelText.style.opacity = "1";
        this.elements.domainModelText.style.transition = "opacity 0.4s ease-in-out";
        
        if (generateUml && domainModelDescription && domainModelDescription.trim()) {
            // Show loading indicator when starting to generate UML
            if (this.elements.umlLoadingIndicator) {
                this.elements.umlLoadingIndicator.classList.remove('d-none');
            }
            
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
    
    // Update the setPlantUML method to apply fade-in animation to PlantUML text
    setPlantUML(plantUML) {
        if (!this.elements.plantumlText) {
            console.error("plantumlText element not found in the DOM");
            return;
        }
        
        // Apply fade-in animation to PlantUML text
        this.elements.plantumlText.style.opacity = "0";
        this.elements.plantumlText.textContent = plantUML;
        
        // Trigger reflow to restart animation
        void this.elements.plantumlText.offsetWidth;
        
        // Apply fade-in
        this.elements.plantumlText.style.opacity = "1";
        this.elements.plantumlText.style.transition = "opacity 0.4s ease-in-out";
        
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

    // Update the renderPlantUMLDiagram method to handle the loading indicator
    renderPlantUMLDiagram(plantUML) {
        if (!plantUML || !plantUML.trim()) {
            // No PlantUML code to render
            this.hideLoadingIndicator();
            
            // Clear the image and show placeholder when there's no PlantUML
            const umlImage = document.getElementById('umlImage');
            const umlPlaceholder = document.getElementById('umlPlaceholder');
            
            if (umlImage && umlPlaceholder) {
                umlImage.classList.add('d-none');
                umlPlaceholder.classList.remove('d-none');
            }
            return;
        }
        
        try {
            // Make sure loading indicator is visible (in case it's called directly)
            if (this.elements.umlLoadingIndicator) {
                this.elements.umlLoadingIndicator.classList.remove('d-none');
            }
            
            // Use the plantumlEncoder library instead of custom encoding
            const encodedUML = plantumlEncoder.encode(plantUML);
            // Use SVG format for better quality
            const imageUrl = `https://www.plantuml.com/plantuml/svg/${encodedUML}`;
                        
            // Find elements
            const umlImage = document.getElementById('umlImage');
            const umlPlaceholder = document.getElementById('umlPlaceholder');
            
            if (umlImage && umlPlaceholder) {
                // Set the image source
                umlImage.src = imageUrl;
                
                // Add loading and error handlers
                umlImage.onload = () => {                  
                    // Hide placeholder
                    umlPlaceholder.classList.add('d-none');
                    
                    // Apply fade-in animation to image
                    umlImage.style.opacity = "0";
                    umlImage.classList.remove('d-none');
                    
                    // Trigger reflow to restart animation
                    void umlImage.offsetWidth;
                    
                    // Apply fade-in
                    umlImage.style.opacity = "1";
                    umlImage.style.transition = "opacity 0.4s ease-in-out";
                    
                    // Hide loading indicator
                    this.hideLoadingIndicator();
                };
                
                umlImage.onerror = () => {
                    console.error("Error loading PlantUML diagram");
                    umlImage.classList.add('d-none');
                    umlPlaceholder.classList.remove('d-none');
                    umlPlaceholder.innerHTML = `
                        <i class="bi bi-exclamation-triangle fs-1 opacity-50 text-warning"></i>
                        <p class="mt-2">Error rendering diagram. Please check your PlantUML syntax.</p>
                    `;
                    this.hideLoadingIndicator();
                };
            } else {
                this.hideLoadingIndicator();
            }
        } catch (error) {
            console.error("Error rendering PlantUML diagram:", error);
            this.hideLoadingIndicator();
        }
    }

    // Add a helper method to hide the loading indicator
    hideLoadingIndicator() {
        if (this.elements.umlLoadingIndicator) {
            this.elements.umlLoadingIndicator.classList.add('d-none');
        }
    }
}