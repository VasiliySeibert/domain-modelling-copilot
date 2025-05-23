class DomainModellingApp {
    constructor() {
        // Initialize views
        this.views = {
            chatView: new ChatView(),
            projectView: new ProjectView(),
            umlView: new UMLView()
        };
        
        // Make the app instance globally accessible for the project view
        window.appInstance = this;
        
        // Add a timer for delayed auto-saving
        this.saveTimeout = null;
        // Flag to track if any interaction has occurred
        this.interactionOccurred = false;
    }

    initialize() {
        // Set up event listeners and initialize components
        this.setupEventListeners();
        this.views.umlView.displayDefaultPlantUML();
        
        // Pass the UMLView instance to the project view
        this.views.projectView.setUmlView(this.views.umlView);
        this.views.projectView.setChatView(this.views.chatView);
        
        // Auto select or create a project on startup
        this.autoSelectProject();
    }
    
    // Update the autoSelectProject method to always create a new project
    autoSelectProject() {
        // Always create a new project instead of selecting an existing one
        fetch("/create_project", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.project_name) {
                    this.views.projectView.selectedProject = data.project_name;
                    console.log(`Created and selected new project: ${data.project_name}`);
                    
                    // Update project display if it exists
                    const currentProjectDisplay = document.getElementById('currentProjectDisplay');
                    if (currentProjectDisplay) {
                        currentProjectDisplay.textContent = data.project_name;
                    }
                }
            });
    }

    setupEventListeners() {
        this.views.chatView.bindSendMessage((message) => {
            this.handleSendMessage(message);
            this.interactionOccurred = true; // Mark that interaction occurred
        });
        this.views.projectView.bindCreateProject();
        this.views.projectView.bindSelectProject();
        this.views.projectView.bindConfirmSelection();
        this.views.umlView.bindGenerateUML();
        
        // Listen for chat messages to trigger auto-save
        document.addEventListener('chatMessageReceived', () => {
            this.interactionOccurred = true;
            this.scheduleSave();
        });
        
        // Listen for domain model updates to trigger auto-save
        document.addEventListener('domainModelUpdated', () => {
            this.interactionOccurred = true;
            this.scheduleSave();
        });
        
        // Listen for UML updates to trigger auto-save
        document.addEventListener('umlUpdated', () => {
            this.interactionOccurred = true;
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

    // Update the save method to only save if interaction occurred
    saveProjectData() {
        const selectedProject = this.views.projectView.selectedProject;
        if (!selectedProject || !this.interactionOccurred) return; // Don't save if no project or no interaction
        
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