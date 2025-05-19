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
            this.fetchProjects().then(() => {
                // Instead of resetting, check if a project is already selected
                if (this.selectedProject) {
                    // If yes, select it in the dropdown
                    this.selectProjectInDropdown(this.selectedProject);
                } else {
                    // If no project is selected, reset the modal
                    this.resetModalState();
                }
            });
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
            
            // Save current project data before switching projects
            const previousProject = document.getElementById('currentProjectDisplay')?.textContent;
            
            if (previousProject && previousProject !== this.selectedProject) {
                // Get current app instance to access save method
                const saveCurrentProject = () => {
                    // Find all app instances in the page
                    const appInstance = window.appInstance;
                    
                    if (appInstance) {
                        // Manually trigger save for the current project
                        appInstance.interactionOccurred = true; // Make sure we save even without explicit interaction
                        appInstance.saveProjectData();
                        console.log("Current project data saved before switching");
                        
                        // Wait a short time to ensure save completes before loading new project
                        setTimeout(() => {
                            // Close modal - using Bootstrap 5 method
                            const modalElement = document.getElementById('projectModal');
                            const modal = bootstrap.Modal.getInstance(modalElement);
                            modal.hide();
                            
                            // Load new project data
                            this.loadProjectData(this.selectedProject);
                        }, 300);
                    } else {
                        console.error("Could not find app instance to save current project");
                        
                        // Still close modal and load project if app instance not found
                        const modalElement = document.getElementById('projectModal');
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        modal.hide();
                        
                        // Load project data
                        this.loadProjectData(this.selectedProject);
                    }
                };
                
                // Execute save
                saveCurrentProject();
            } else {
                // If no previous project or same project, just load
                // Close modal - using Bootstrap 5 method
                const modalElement = document.getElementById('projectModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                modal.hide();
                
                // Load project data
                this.loadProjectData(this.selectedProject);
            }
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
    
    // Update the fetchProjects method to select the current project in the dropdown
    fetchProjects() {
        return fetch("/get_projects")
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    this.populateProjectsDropdown(data.projects);
                    
                    // If a project is already selected, select it in the dropdown
                    if (this.selectedProject) {
                        this.selectProjectInDropdown(this.selectedProject);
                    }
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

    selectProjectInDropdown(projectName) {
        // Find and select the option with the matching value
        const options = this.elements.existingProjects.options;
        for (let i = 0; i < options.length; i++) {
            if (options[i].value === projectName) {
                this.elements.existingProjects.selectedIndex = i;
                
                // Enable the confirm button
                this.elements.confirmSelectionBtn.disabled = false;
                
                // Show rename section and populate with current name
                this.elements.renameProjectSection.style.display = "block";
                this.elements.newProjectName.value = projectName;
                break;
            }
        }
    }
}