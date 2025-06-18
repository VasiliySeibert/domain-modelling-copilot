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
        
        // Only keep the loading state flag
        this.isLoadingState = false;

        // Add flag to track if undo is available
        this.undoAvailable = false;
    }

    initialize() {
        this.setupEventListeners();
        this.views.umlView.displayDefaultPlantUML();
        
        this.views.projectView.setUmlView(this.views.umlView);
        this.views.projectView.setChatView(this.views.chatView);
        
        this.autoSelectProject();
    }
    
    autoSelectProject() {
        fetch("/create_project", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.project_name) {
                    this.views.projectView.selectedProject = data.project_name;
                    
                    const selectProjectBtn = document.getElementById('selectProjectBtn');
                    if (selectProjectBtn) {
                        selectProjectBtn.innerHTML = `<i class="bi bi-folder-check me-1"></i> ${data.project_name}`;
                    }

                    this.isLoadingState = true;
                    
                    this.views.projectView.loadProjectData(data.project_name)
                        .catch(err => {
                            console.error("Error during initial project load:", err);
                            alert("Error loading initial project data. Please check console.");
                        })
                        .finally(() => {
                            this.isLoadingState = false;
                        });
                }
            })
            .catch(err => {
                console.error("Failed to create or select initial project:", err);
                alert("Error: Could not initialize project. Please check the console and try refreshing.");
            });
    }

    setupEventListeners() {
        this.views.chatView.bindSendMessage((message) => {
            this.handleSendMessage(message);
        });
        
        this.views.projectView.bindCreateProject();
        this.views.projectView.bindSelectProject();
        this.views.projectView.bindConfirmSelection();
        this.views.umlView.bindGenerateUML();
        
        const undoButton = document.getElementById('undoChangeBtn');
        if (undoButton) {
            undoButton.addEventListener('click', () => this.handleUndoChange());
        }
    }
    
    handleUndoChange() {
        const selectedProject = this.views.projectView.selectedProject;
        if (!selectedProject) {
            alert("Please select a project first.");
            return;
        }

        if (!confirm(`Are you sure you want to undo the last change to your domain model?`)) {
            return;
        }

        const undoButton = document.getElementById('undoChangeBtn');
        undoButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
        undoButton.disabled = true;

        fetch("/undo_project_change", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_name: selectedProject }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(`Error undoing version: ${data.error}`);
                
                // If we can't undo any further, disable the button
                if (data.error.includes("Cannot undo the initial project version")) {
                    undoButton.disabled = true;
                }
            } else if (data.project_data) {
                // Success message as toast or small notification instead of alert
                console.log("Project reverted to previous version");
                
                this.isLoadingState = true;
                this.undoAvailable = false; // Mark that undo is no longer available

                this.views.projectView.loadProjectData(selectedProject, data.project_data)
                    .catch(loadErr => {
                        console.error("Error loading project data in undo:", loadErr);
                    })
                    .finally(() => {
                        this.isLoadingState = false;
                        console.log('handleUndoChange: isLoadingState reset after loadProjectData completed');
                    });
                
                // Get project versions to determine if there's only one left
                fetch(`/get_project_data?project_name=${encodeURIComponent(selectedProject)}`)
                    .then(response => response.json())
                    .then(projectInfo => {
                        // Check if we need to disable the undo button (only 1 version remains)
                        const versions = projectInfo.project_data?.versions || [];
                        if (versions.length <= 1) {
                            undoButton.disabled = true;
                        }
                    })
                    .catch(err => console.error("Error checking versions:", err));
            }
        })
        .catch(err => {
            alert("An unexpected error occurred while undoing change.");
            console.error("Undo error:", err);
            this.enableUndoButton();
        });
    }
    
    // Add helper method to enable the undo button
    enableUndoButton() {
        const undoButton = document.getElementById('undoChangeBtn');
        if (undoButton) {
            undoButton.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i>';
            undoButton.disabled = false;
            this.undoAvailable = true;
        }
    }
    
    handleSendMessage(message) {
        if (!message) return;

        const selectedProject = this.views.projectView.selectedProject;
        if (!selectedProject) {
            alert("Please select a project before sending a message.");
            this.views.chatView.enableInput();
            return;
        }

        this.views.chatView.display_input(message);
        this.views.chatView.clearInput();
        this.views.chatView.disableInput();
        const loadingIndicator = this.views.chatView.showLoadingIndicator();

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                message: message,
                project_name: selectedProject // Include project name with every chat request
            }),
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
                // Only update if there's actually content in the domain model
                if (data.domain_model_description && data.domain_model_description.trim()) {
                    this.views.umlView.setDomainModelDescription(data.domain_model_description, false);
                }
                
                this.views.chatView.displayBotMessage(data.suggestion || data.response);
                
                // Update PlantUML if provided
                if (data.plant_uml && data.plant_uml.trim()) {
                    this.views.umlView.setPlantUML(data.plant_uml);
                }
                
                this.views.chatView.showActionButtons();
                
                // Enable undo button when we get a response that changes the domain model
                this.enableUndoButton();
            } else {
                // General response
                this.views.chatView.displayBotMessage(data.response || "No response provided.");
                
                // Only update domain model if not empty or undefined
                if (data.domain_model_description && data.domain_model_description.trim()) {
                    this.views.umlView.setDomainModelDescription(data.domain_model_description, false);
                    
                    // Enable undo button when domain model changes
                    this.enableUndoButton();
                }
                
                // Only update PlantUML if provided and not empty
                if (data.plant_uml && data.plant_uml.trim()) {
                    this.views.umlView.setPlantUML(data.plant_uml);
                    
                    // Enable undo button when PlantUML changes
                    this.enableUndoButton();
                }
            }

            // Enable undo button when we get a response that changes the domain model
            if (data.domain_model_description || data.plant_uml) {
                this.enableUndoButton();
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
    
    enableUndoButton() {
        const undoButton = document.getElementById('undoChangeBtn');
        if (undoButton) {
            undoButton.disabled = false;
        }
    }
}