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
        this.umlView = null;
        this.chatView = null;

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
    
    // Add these methods to set the view instances
    setUmlView(umlView) {
        this.umlView = umlView;
    }
    
    setChatView(chatView) {
        this.chatView = chatView;
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
            
            const appInstance = window.appInstance; // Access the global app instance
            const currentProjectName = this.selectedProject;

            const loadNewProjectData = () => {
                const modalElement = document.getElementById('projectModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }

                if (appInstance) {
                    appInstance.isLoadingState = true;
                    console.log('bindConfirmSelection: isLoadingState = true before loadProjectData');
                }
                
                this.loadProjectData(currentProjectName) // This now returns a Promise
                    .catch(err => {
                        console.error("Error during loadProjectData in project switch:", err);
                        // Alert or handle error appropriately
                    })
                    .finally(() => {
                        if (appInstance) {
                            appInstance.isLoadingState = false;
                            console.log('bindConfirmSelection: isLoadingState = false (completed)');
                        }
                    });
            };
            
            // Remove auto-saving previous project logic and directly load new project
            loadNewProjectData();
        });
    }
    
    // Update the loadProjectData method to use the shared UMLView instance
    // Allow passing projectData directly to avoid a fetch if data is already available (e.g., after undo)
    // Ensure it returns a Promise
    loadProjectData(projectName, directData = null) {
        const displayData = (projectData) => {
            // Update domain model description if available
            if (projectData.domain_model_description !== undefined) { // Check for undefined to allow empty string
                document.getElementById("domainModelText").textContent = projectData.domain_model_description;
                document.dispatchEvent(new CustomEvent('domainModelUpdated'));
            } else {
                 document.getElementById("domainModelText").textContent = "No domain model description available.";
            }
            
            // Update PlantUML if available - use the shared UMLView instance
            if (projectData.plant_uml !== undefined && this.umlView) {
                this.umlView.setPlantUML(projectData.plant_uml);
            } else if (this.umlView) {
                this.umlView.setPlantUML(""); // Clear PlantUML if not available
            }
            
            // Update chat history if available
            const chatBox = document.getElementById("chatBox");
            chatBox.innerHTML = ""; // Clear existing messages
            if (projectData.chat_history && projectData.chat_history.length > 0 && this.chatView) {
                projectData.chat_history.forEach(msg => {
                    if (msg.role === "user") {
                        this.chatView.display_input(msg.content);
                    } else {
                        this.chatView.displayBotMessage(msg.content);
                    }
                });
            } else if (this.chatView) {
                // Display a default message if chat history is empty
                this.chatView.displayBotMessage("Chat history is empty for this version.");
            }
            
            // Update project name display on the select project button
            const selectProjectBtn = document.getElementById('selectProjectBtn');
            if (selectProjectBtn) {
                selectProjectBtn.innerHTML = `<i class="bi bi-folder-check me-1"></i> ${projectName}`;
            }

            // Show success notification
            const successNotification = document.createElement('div');
            successNotification.className = 'toast-notification';
            successNotification.innerHTML = `
                <i class="bi bi-check-circle-fill"></i>
                Project "${projectName}" loaded successfully
            `;
            document.body.appendChild(successNotification);
            
            setTimeout(() => {
                if (document.body.contains(successNotification)) {
                    document.body.removeChild(successNotification);
                }
            }, 3000);
        };

        if (directData) {
            try {
                displayData(directData);
                const loadingIndicator = document.querySelector('.project-switching-indicator');
                if (loadingIndicator && document.body.contains(loadingIndicator)) {
                    document.body.removeChild(loadingIndicator);
                }
                return Promise.resolve(); // Return a resolved promise
            } catch (e) {
                console.error("Error displaying direct data:", e);
                return Promise.reject(e); // Return a rejected promise
            }
        }

        // Show loading indicator for fetch
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'project-switching-indicator';
        loadingIndicator.innerHTML = `
            <div class="spinner"></div>
            <div>Loading project "${projectName}"...</div>
        `;
        document.body.appendChild(loadingIndicator);
        
        return fetch(`/get_project_data?project_name=${encodeURIComponent(projectName)}`)
            .then((response) => {
                if (!response.ok) {
                    // Attempt to parse error from JSON response, otherwise use status text
                    return response.json().then(errData => {
                        throw new Error(errData.error || response.statusText);
                    }).catch(() => {
                        throw new Error(response.statusText);
                    });
                }
                return response.json();
            })
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                    throw new Error(data.error); // Make sure to throw to propagate to catch/finally
                } else if (data.project_data) {
                    displayData(data.project_data);
                }
            })
            // Catch is handled by the caller if needed
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