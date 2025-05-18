/**
 * Domain Modelling Copilot - Frontend JavaScript
 * MVC Architecture Implementation
 */

// Main application initialization
// document.addEventListener("DOMContentLoaded", () => {
//     // Initialize the application
//     const app = new DomainModellingApp();
//     app.initialize();
// });

/**
 * Main Application Controller
 */
class DomainModellingApp {
    constructor() {
        // Initialize views
        this.views = {
            chatView: new ChatView(),
            projectView: new ProjectView(),
            umlView: new UMLView()
        };
        
        // Add a timer for delayed auto-saving
        this.saveTimeout = null;
    }

    initialize() {
        // Set up event listeners and initialize components
        this.setupEventListeners();
        this.views.umlView.displayDefaultPlantUML();
        this.views.projectView.fetchProjects();
    }

    setupEventListeners() {
        this.views.chatView.bindSendMessage((message) => this.handleSendMessage(message));
        this.views.projectView.bindCreateProject();
        this.views.projectView.bindSelectProject();
        this.views.projectView.bindConfirmSelection();
        this.views.umlView.bindGenerateUML();
        
        // Listen for chat messages to trigger auto-save
        document.addEventListener('chatMessageReceived', () => {
            this.scheduleSave();
        });
        
        // Listen for domain model updates to trigger auto-save
        document.addEventListener('domainModelUpdated', () => {
            this.scheduleSave();
        });
        
        // Listen for UML updates to trigger auto-save
        document.addEventListener('umlUpdated', () => {
            this.scheduleSave();
        });
    }

    // Add a debounced save method to avoid excessive database calls
    scheduleSave() {
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        
        // Wait 2 seconds after last change before saving
        this.saveTimeout = setTimeout(() => {
            this.saveProjectData();
        }, 2000);
    }
    
    handleSendMessage(message) {
        if (!message) return;

        // Display user's message and show loading state
        this.views.chatView.display_input(message);
        this.views.chatView.clearInput();
        this.views.chatView.disableInput();
        const loadingIndicator = this.views.chatView.showLoadingIndicator();

        // Send request to backend
        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then((data) => {
                loadingIndicator.remove();

                if (data.error) {
                    this.views.chatView.displayErrorMessage(data.error);
                } else if (data.domain_model_description) {
                    // Display domain model description and suggestion
                    this.views.umlView.setDomainModelDescription(data.domain_model_description);
                    this.views.chatView.displayBotMessage(data.suggestion);
                    this.views.chatView.showActionButtons();
                } else {
                    // General response
                    this.views.chatView.displayBotMessage(data.response || "No response provided.");
                    
                    // Dispatch an event for chat message received
                    document.dispatchEvent(new CustomEvent('chatMessageReceived'));
                }
            })
            .catch((err) => {
                loadingIndicator.remove();
                this.views.chatView.displayErrorMessage("An error occurred while processing your request. Please try again.");
                console.error("Error:", err);
            })
            .finally(() => {
                this.views.chatView.enableInput();
            });
    }

    saveProjectData() {
        const selectedProject = this.views.projectView.selectedProject;
        if (!selectedProject) return; // No project selected
        
        const domainModelDescription = this.views.umlView.getDomainModelDescriptionText();
        const plantUml = this.views.umlView.getPlantUMLText();
        const chatHistory = this.views.chatView.getChatHistory();
        
        // Add a subtle indicator for saving
        const savingIndicator = document.createElement('div');
        savingIndicator.classList.add('saving-indicator');
        savingIndicator.textContent = 'Saving...';
        document.body.appendChild(savingIndicator);
        
        fetch("/save_project_data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                project_name: selectedProject,
                domain_model_description: domainModelDescription !== "No detailed description provided." ? domainModelDescription : null,
                plant_uml: plantUml !== "" ? plantUml : null,
                chat_history: chatHistory
            })
        })
        .then(response => {
            // Remove the saving indicator
            setTimeout(() => {
                document.body.removeChild(savingIndicator);
            }, 1000);
            
            // Optional - log save success
            if (response.ok) {
                console.log("Project data saved automatically");
            }
        })
        .catch(err => {
            console.error("Error saving project data:", err);
            // Remove the saving indicator
            document.body.removeChild(savingIndicator);
        });
    }
}

/**
 * Remove SessionModel class
 */
// class SessionModel { ... }

/**
 * Chat View
 */
class ChatView {
    constructor() {
        this.elements = {
            chatBox: document.getElementById("chatBox"),
            userInput: document.getElementById("userInput"),
            sendButton: document.getElementById("sendButton"),
           
            actionButtons: document.getElementById("actionButtons")
        };
    }
    
    
    bindSendMessage(handler) {
        // Button click handler
        this.elements.sendButton.addEventListener("click", () => {
            handler(this.elements.userInput.value.trim());
        });
        
        // Enter key handler
        this.elements.userInput.addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                handler(this.elements.userInput.value.trim());
            }
        });
    }
    
    display_input(message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", "user-message");
        messageDiv.textContent = message;
        this.elements.chatBox.appendChild(messageDiv);
        this.autoScrollChatBox();
    }
    
    displayBotMessage(content) {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.classList.add("chat-message", "bot-message");
        botMessageDiv.innerHTML = marked.parse(content);
        this.elements.chatBox.appendChild(botMessageDiv);
        this.autoScrollChatBox();
        
        // Dispatch event for chat message received
        document.dispatchEvent(new CustomEvent('chatMessageReceived'));
    }
    
    displayErrorMessage(errorText) {
        const errorDiv = document.createElement("div");
        errorDiv.classList.add("chat-message", "error-message");
        errorDiv.textContent = errorText;
        this.elements.chatBox.appendChild(errorDiv);
        this.autoScrollChatBox();
    }
    
    showLoadingIndicator() {
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("chat-message", "loading-message");
        loadingDiv.innerHTML = `<span class="loading-dots"><span></span><span></span><span></span></span>`;
        this.elements.chatBox.appendChild(loadingDiv);
        this.autoScrollChatBox();
        return loadingDiv;
    }
    
    clearInput() {
        this.elements.userInput.value = "";
    }
    
    disableInput() {
        this.elements.userInput.disabled = true;
        this.elements.sendButton.disabled = true;
    }
    
    enableInput() {
        this.elements.userInput.disabled = false;
        this.elements.sendButton.disabled = false;
        this.elements.userInput.focus();
    }
    
    autoScrollChatBox() {
        this.elements.chatBox.scrollTop = this.elements.chatBox.scrollHeight;
    }
    
    showActionButtons() {
        this.elements.actionButtons.style.visibility = "visible";
        this.elements.actionButtons.style.opacity = "1";
    }
    
    hideActionButtons() {
        this.elements.actionButtons.style.visibility = "hidden";
        this.elements.actionButtons.style.opacity = "0";
    }
    
    getChatHistory() {
        const chatHistory = [];
        document.querySelectorAll(".chat-message").forEach(msg => {
            if (msg.classList.contains("user-message")) {
                chatHistory.push({
                    "role": "user", 
                    "content": msg.textContent.trim()
                });
            } else if (msg.classList.contains("bot-message")) {
                chatHistory.push({
                    "role": "assistant", 
                    "content": msg.textContent.trim()
                });
            }
        });
        return chatHistory;
    }
}

/**
 * Project View - Simplified to remove file-level management
 */
class ProjectView {
    constructor() {
        this.elements = {
            existingProjects: document.getElementById("existingProjects"),
            newProjectName: document.getElementById("newProjectName"),
            renameProjectBtn: document.getElementById("renameProjectBtn"),
            renameProjectSection: document.getElementById("renameProjectSection"),
            createNewProjectBtn: document.getElementById("createNewProjectBtn"),
            confirmSelectionBtn: document.getElementById("confirmSelectionBtn"),
            projectModal: document.getElementById("projectModal")
        };
        
        this.selectedProject = null;

        // Add event listener for modal opening
        document.getElementById('projectModal').addEventListener('show.bs.modal', () => {
            this.fetchProjects();
            
            // Reset modal state
            this.resetModalState();
        });
    }
    
    bindCreateProject() {
        // Create new project button - auto-generated name
        this.elements.createNewProjectBtn.addEventListener("click", () => {
            // Show loading indicator
            this.elements.createNewProjectBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
            this.elements.createNewProjectBtn.disabled = true;
            
            fetch("/create_project", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({})  // No data needed as name is auto-generated
            })
                .then((response) => response.json())
                .then((data) => {
                    // Reset button state
                    this.elements.createNewProjectBtn.innerHTML = '<i class="bi bi-plus-circle me-1"></i>New Project';
                    this.elements.createNewProjectBtn.disabled = false;
                    
                    if (data.error) {
                        alert(data.error);
                    } else {
                        // Auto-select the newly created project
                        this.fetchProjects().then(() => {
                            this.selectProject(data.project_name);
                        });
                    }
                })
                .catch((err) => {
                    // Reset button state on error
                    this.elements.createNewProjectBtn.innerHTML = '<i class="bi bi-plus-circle me-1"></i>New Project';
                    this.elements.createNewProjectBtn.disabled = false;
                    
                    console.error("Error creating project:", err);
                    alert("An error occurred while creating the project.");
                });
        });
    }
    
    bindSelectProject() {
        // Handle project selection from dropdown
        this.elements.existingProjects.addEventListener("change", (event) => {
            const projectName = event.target.value;
            if (!projectName) {
                this.selectedProject = null;
                this.elements.confirmSelectionBtn.disabled = true;
                this.elements.renameProjectSection.style.display = "none";
                return;
            }
            
            this.selectedProject = projectName;
            this.elements.confirmSelectionBtn.disabled = false;
            
            // Show rename section when a project is selected
            this.elements.renameProjectSection.style.display = "block";
            this.elements.newProjectName.value = projectName;
            this.elements.newProjectName.focus();
        });
        
        // Handle rename project button
        this.elements.renameProjectBtn.addEventListener("click", () => {
            const oldProjectName = this.selectedProject;
            const newProjectName = this.elements.newProjectName.value.trim();
            
            if (!oldProjectName || !newProjectName) {
                alert("Please select a project and enter a new name.");
                return;
            }
            
            // Show loading indicator
            this.elements.renameProjectBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Renaming...';
            this.elements.renameProjectBtn.disabled = true;
            
            fetch("/rename_project", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    old_project_name: oldProjectName,
                    new_project_name: newProjectName 
                }),
            })
                .then((response) => response.json())
                .then((data) => {
                    // Reset button state
                    this.elements.renameProjectBtn.innerHTML = 'Rename';
                    this.elements.renameProjectBtn.disabled = false;
                    
                    if (data.error) {
                        alert(data.error);
                    } else {
                        // Refresh projects and select the renamed one
                        this.fetchProjects().then(() => {
                            this.selectProject(newProjectName);
                        });
                    }
                })
                .catch((err) => {
                    // Reset button state on error
                    this.elements.renameProjectBtn.innerHTML = 'Rename';
                    this.elements.renameProjectBtn.disabled = false;
                    
                    console.error("Error renaming project:", err);
                    alert("An error occurred while renaming the project.");
                });
        });
    }
    
    bindConfirmSelection() {
        // Handle confirm button click
        this.elements.confirmSelectionBtn.addEventListener("click", () => {
            // Get the final selected project
            if (!this.selectedProject) {
                alert("Please select a project.");
                return;
            }
            
            // Close modal - using Bootstrap 5 method
            const modalElement = document.getElementById('projectModal');
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();
            
            // Show confirmation
            alert(`Selected project: "${this.selectedProject}"`);
            
            // Load project data
            this.loadProjectData(this.selectedProject);
        });
    }
    
    loadProjectData(projectName) {
        // Show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'project-loading';
        loadingIndicator.innerHTML = `
            <div class="d-flex flex-column align-items-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">Loading project data...</span>
                </div>
                <div>Loading project data...</div>
            </div>
        `;
        document.body.appendChild(loadingIndicator);
        
        fetch(`/get_project_data?project_name=${encodeURIComponent(projectName)}`)
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else if (data.project_data) {
                    // Update the UI with project data
                    const projectData = data.project_data;
                    
                    // Update domain model description if available
                    if (projectData.domain_model_description) {
                        document.getElementById("domainModelText").textContent = projectData.domain_model_description;
                        
                        // Dispatch event that domain model was updated
                        document.dispatchEvent(new CustomEvent('domainModelUpdated'));
                    }
                    
                    // Update PlantUML if available
                    if (projectData.plant_uml) {
                        document.getElementById("plantumlText").textContent = projectData.plant_uml;
                        
                        // Render the PlantUML diagram
                        const umlView = new UMLView();
                        umlView.renderPlantUMLDiagram(projectData.plant_uml);
                        
                        // Dispatch event that UML was updated
                        document.dispatchEvent(new CustomEvent('umlUpdated'));
                    }
                    
                    // Update chat history if available
                    if (projectData.chat_history && projectData.chat_history.length > 0) {
                        const chatBox = document.getElementById("chatBox");
                        chatBox.innerHTML = ""; // Clear existing messages
                        
                        // Add each message to the chat box
                        projectData.chat_history.forEach(msg => {
                            const messageDiv = document.createElement("div");
                            messageDiv.classList.add("chat-message");
                            
                            if (msg.role === "user") {
                                messageDiv.classList.add("user-message");
                                messageDiv.textContent = msg.content;
                            } else {
                                messageDiv.classList.add("bot-message");
                                messageDiv.innerHTML = marked.parse(msg.content);
                            }
                            
                            chatBox.appendChild(messageDiv);
                        });
                        
                        // Auto-scroll to the bottom of chat
                        chatBox.scrollTop = chatBox.scrollHeight;
                    }
                    
                    // Show success notification
                    const successNotification = document.createElement('div');
                    successNotification.className = 'toast-notification';
                    successNotification.innerHTML = `
                        <i class="bi bi-check-circle-fill"></i>
                        Project "${projectName}" loaded successfully
                    `;
                    document.body.appendChild(successNotification);
                    
                    // Remove notification after animation completes
                    setTimeout(() => {
                        if (document.body.contains(successNotification)) {
                            document.body.removeChild(successNotification);
                        }
                    }, 3000);
                }
            })
            .catch((err) => {
                console.error("Error loading project data:", err);
                alert("An error occurred while loading project data.");
            })
            .finally(() => {
                // Remove loading indicator
                if (document.body.contains(loadingIndicator)) {
                    document.body.removeChild(loadingIndicator);
                }
            });
    }
    
    selectProject(projectName) {
        // Helper method to auto-select a project in the dropdown
        const options = this.elements.existingProjects.options;
        for (let i = 0; i < options.length; i++) {
            if (options[i].value === projectName) {
                this.elements.existingProjects.selectedIndex = i;
                break;
            }
        }
        
        this.selectedProject = projectName;
        this.elements.confirmSelectionBtn.disabled = false;
        
        // Show rename section
        this.elements.renameProjectSection.style.display = "block";
        this.elements.newProjectName.value = projectName;
    }
    
    fetchProjects() {
        return fetch("/get_projects")
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    this.populateProjectsDropdown(data.projects);
                }
                return data;
            })
            .catch((err) => {
                console.error("Error fetching projects:", err);
                alert("An error occurred while fetching projects.");
            });
    }
    
    populateProjectsDropdown(projects) {
        this.elements.existingProjects.innerHTML = '<option value="" disabled selected>Select a project</option>';
        if (projects && projects.length > 0) {
            projects.forEach((project) => {
                const option = document.createElement("option");
                option.value = project;
                option.textContent = project;
                this.elements.existingProjects.appendChild(option);
            });
        } else {
            const option = document.createElement("option");
            option.disabled = true;
            option.textContent = "No projects found";
            this.elements.existingProjects.appendChild(option);
        }
    }
    
    getProjectData() {
        return {
            projectName: this.selectedProject
        };
    }

    resetModalState() {
        // Reset modal to initial state
        this.selectedProject = null;
        this.elements.existingProjects.selectedIndex = 0;
        this.elements.newProjectName.value = "";
        this.elements.confirmSelectionBtn.disabled = true;
        this.elements.renameProjectSection.style.display = "none";
    }
}

/**
 * UML View - Modified to generate PlantUML from scenario text
 */
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

document.addEventListener('DOMContentLoaded', function() {
    // Initialize app only after DOM is loaded
    const app = new DomainModellingApp();
    app.initialize();
});