/**
 * Domain Modelling Copilot - Frontend JavaScript
 * MVC Architecture Implementation
 */

// Main application initialization
document.addEventListener("DOMContentLoaded", () => {
    // Initialize the application
    const app = new DomainModellingApp();
    app.initialize();
});

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
        
        // Initialize session model
        this.sessionModel = new SessionModel();
    }

    initialize() {
        // Load saved username
        const savedName = this.sessionModel.getSavedName();
        if (savedName) {
            this.views.chatView.setUsername(savedName);
        }

        // Set up event listeners and initialize components
        this.setupEventListeners();
        this.views.umlView.displayDefaultPlantUML();
        this.views.projectView.fetchProjects();
    }

    setupEventListeners() {
        // Bind all event handlers
        this.views.chatView.bindSubmitName((name) => this.handleNameSubmission(name));
        this.views.chatView.bindSendMessage((message) => this.handleSendMessage(message));
        this.views.projectView.bindCreateProject();
        this.views.projectView.bindSelectProject();
        this.views.projectView.bindCreateFile();
        this.views.projectView.bindConfirmSelection();
        this.views.umlView.bindGenerateUML();
        
        // Database submission
        this.views.projectView.bindSubmitToDatabase(() => ({
            project_name: this.views.projectView.getProjectData().projectName,
            file_name: this.views.projectView.getProjectData().fileName,
            username: this.sessionModel.getSavedName() || "Anonymous",
            scenario: this.views.umlView.getScenarioText() === "No detailed description provided." ? null : this.views.umlView.getScenarioText(),
            plant_uml: this.views.umlView.getPlantUMLText() === "" ? null : this.views.umlView.getPlantUMLText(),
            chat_history: this.views.chatView.getChatHistory()
        }));
    }

    handleNameSubmission(name) {
        if (!name) {
            alert("Please enter a name.");
            return;
        }

        this.sessionModel.saveName(name);

        fetch("/submit_name", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert("Name saved successfully! You can now start chatting.");
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while saving the name.");
            });
    }

    handleSendMessage(message) {
        if (!message) return;

        const userName = this.sessionModel.getSavedName();
        if (!userName) {
            alert("Please enter your name before starting the chat.");
            return;
        }

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
                } else if (data.scenario) {
                    // Display domain model description and suggestion
                    this.views.umlView.setScenario(data.scenario);
                    this.views.chatView.displayBotMessage(data.suggestion); // Updated from "suggestion" to "suggestion"
                    this.views.chatView.showActionButtons();
                } else {
                    // General response
                    this.views.chatView.displayBotMessage(data.response || "No response provided.");
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
}

/**
 * Session Model
 */
class SessionModel {
    constructor() {
        this.storage = sessionStorage;
    }
    
    getSavedName() {
        return this.storage.getItem("userName");
    }
    
    saveName(name) {
        this.storage.setItem("userName", name);
    }
}

/**
 * Chat View
 */
class ChatView {
    constructor() {
        this.elements = {
            chatBox: document.getElementById("chatBox"),
            userInput: document.getElementById("userInput"),
            sendButton: document.getElementById("sendButton"),
            userNameInput: document.getElementById("userName"),
            submitNameBtn: document.getElementById("submitNameBtn"),
            actionButtons: document.getElementById("actionButtons")
        };
    }
    
    bindSubmitName(handler) {
        this.elements.submitNameBtn.addEventListener("click", () => {
            handler(this.elements.userNameInput.value.trim());
        });
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
    
    setUsername(name) {
        this.elements.userNameInput.value = name;
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
 * Project View
 */
class ProjectView {
    constructor() {
        this.elements = {
            existingProjects: document.getElementById("existingProjects"),
            newProjectName: document.getElementById("newProjectName"),
            createProjectBtn: document.getElementById("createProjectBtn"),
            projectFiles: document.getElementById("projectFiles"),
            createFileBtn: document.getElementById("createFileBtn"),
            confirmSelectionBtn: document.getElementById("confirmSelectionBtn"),
            saveToDatabaseBtn: document.getElementById("saveToDatabaseBtn"), // FIXED: use correct ID
            // New elements for improved UI
            projectSelectionStep: document.getElementById("projectSelectionStep"),
            fileSelectionStep: document.getElementById("fileSelectionStep"),
            nextToFileSelectionBtn: document.getElementById("nextToFileSelectionBtn"),
            backToProjectSelectionBtn: document.getElementById("backToProjectSelectionBtn"),
            selectedProjectName: document.getElementById("selectedProjectName"),
            projectModal: document.getElementById("projectModal")
        };
        
        this.selectedProject = null;
        this.selectedFile = null;

        // Add event listener for modal opening right away
        document.getElementById('projectModal').addEventListener('show.bs.modal', () => {
            this.fetchProjects();
            
            // Reset modal state
            this.elements.projectSelectionStep.classList.remove("d-none");
            this.elements.fileSelectionStep.classList.add("d-none");
            this.elements.confirmSelectionBtn.disabled = true;
        });
    }
    
    bindCreateProject() {
        // Existing code remains the same
        this.elements.createProjectBtn.addEventListener("click", () => {
            const projectName = this.elements.newProjectName.value.trim();
            if (!projectName) {
                alert("Please enter a project name.");
                return;
            }

            fetch("/create_project", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ project_name: projectName }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        alert("Project created successfully!");
                        this.elements.newProjectName.value = ""; // Clear the input field
                        this.fetchProjects(); // Refresh the projects dropdown
                        
                        // Auto-select the newly created project
                        setTimeout(() => {
                            this.selectProject(projectName);
                        }, 100);
                    }
                })
                .catch((err) => {
                    console.error("Error creating project:", err);
                    alert("An error occurred while creating the project.");
                });
        });
        
        // Enable next button when project name is typed
        this.elements.newProjectName.addEventListener("input", () => {
            this.elements.nextToFileSelectionBtn.disabled = !this.elements.newProjectName.value.trim();
        });
    }
    
    bindSelectProject() {
        // Enable next button when a project is selected from dropdown
        this.elements.existingProjects.addEventListener("change", (event) => {
            const projectName = event.target.value;
            if (!projectName) return;
            
            this.selectedProject = projectName;
            this.elements.nextToFileSelectionBtn.disabled = false;
        });
        
        // Handle next button click to go to file selection
        this.elements.nextToFileSelectionBtn.addEventListener("click", () => {
            let projectName;
            
            // Check if selection is from dropdown or input field
            if (this.elements.existingProjects.value) {
                projectName = this.elements.existingProjects.value;
            } else if (this.elements.newProjectName.value.trim()) {
                projectName = this.elements.newProjectName.value.trim();
            } else {
                alert("Please select an existing project or enter a new project name.");
                return;
            }
            
            // Always update selectedProject to keep it consistent
            this.selectedProject = projectName;
            
            // Update selected project display and move to step 2
            this.elements.selectedProjectName.textContent = projectName;
            this.elements.projectSelectionStep.classList.add("d-none");
            this.elements.fileSelectionStep.classList.remove("d-none");
            
            // Fetch files for the selected project
            this.fetchFiles(projectName);
            
            // Rebind the create file button with the current project context
            this.bindCreateFile();
        });
        
        // Handle back button click to return to project selection
        this.elements.backToProjectSelectionBtn.addEventListener("click", () => {
            this.elements.fileSelectionStep.classList.add("d-none");
            this.elements.projectSelectionStep.classList.remove("d-none");
            this.elements.confirmSelectionBtn.disabled = true;
        });
        
        // Reset modal when closed
        this.elements.projectModal.addEventListener('hidden.bs.modal', () => {
            this.resetModalState();
        });

        // Refresh projects when modal opens
        document.getElementById('projectModal').addEventListener('show.bs.modal', () => {
            this.fetchProjects();
            
            // Reset modal state
            this.elements.projectSelectionStep.classList.remove("d-none");
            this.elements.fileSelectionStep.classList.add("d-none");
            this.elements.confirmSelectionBtn.disabled = true;
        });
    }
    
    bindCreateFile() {
        // Remove any existing event listener to prevent duplicates
        const createFileBtn = this.elements.createFileBtn;
        const newCreateFileBtn = createFileBtn.cloneNode(true);
        createFileBtn.parentNode.replaceChild(newCreateFileBtn, createFileBtn);
        this.elements.createFileBtn = newCreateFileBtn;
        
        // Add event listener with debugging
        this.elements.createFileBtn.addEventListener("click", () => {
            
            // Get project name directly from the selectedProject variable 
            // which is set during the transition to step 2
            const projectName = this.selectedProject;
            
            
            if (!projectName) {
                alert("Please select a project first.");
                return;
            }

            const fileName = prompt("Enter the file name:");
            if (!fileName || !fileName.trim()) {
                alert("File name cannot be empty.");
                return;
            }

            // Add spinner or indication that request is processing
            this.elements.createFileBtn.disabled = true;
            this.elements.createFileBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';

            fetch("/create_file", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ project_name: projectName, file_name: fileName }),
            })
                .then(response => {
                    return response.json();
                })
                .then(data => {
                    this.elements.createFileBtn.disabled = false;
                    this.elements.createFileBtn.textContent = "Create New File";
                    
                    if (data.error) {
                        alert(data.error);
                    } else {
                        alert("File created successfully!");
                        this.fetchFiles(projectName); // Refresh the file list
                    }
                })
                .catch(err => {
                    console.error("Error creating file:", err);
                    this.elements.createFileBtn.disabled = false;
                    this.elements.createFileBtn.textContent = "Create New File";
                    alert("An error occurred while creating the file.");
                });
        });
    }
    
    bindConfirmSelection() {
        // Ensure we have the DOM element
        if (!this.elements.projectFiles) {
          console.error("Project files select element not found");
          return;
        }
        
        // Make sure we can detect file selection changes
        this.elements.projectFiles.addEventListener("change", (event) => {
          const fileSelected = !!event.target.value;
          this.selectedFile = event.target.value;
          this.elements.confirmSelectionBtn.disabled = !fileSelected;
        });
        
        // Handle confirm button click
        this.elements.confirmSelectionBtn.addEventListener("click", () => {
          // Get the final selected project and file
          const selectedProject = this.selectedProject || this.elements.selectedProjectName.textContent;
          const selectedFile = this.selectedFile || this.elements.projectFiles.value;
          
          if (!selectedProject || !selectedFile) {
            alert("Please select both a project and a file.");
            return;
          }
          
          // Store selections
          this.selectedProject = selectedProject;
          this.selectedFile = selectedFile;
          
          // Close modal - using Bootstrap 5 method
          const modalElement = document.getElementById('projectModal');
          const modal = bootstrap.Modal.getInstance(modalElement);
          modal.hide();
          
          // Show confirmation using alert
          alert(`Selected: Project "${selectedProject}", File "${selectedFile}"`);
          
          // Display is removed as requested - we're not adding anything to the header
        });
    }
    
    bindSubmitToDatabase(handler) {
        // Use element from the class properties
        if (!this.elements.saveToDatabaseBtn) {
            console.error("Save to Database button not found");
            return;
        }
        
        this.elements.saveToDatabaseBtn.addEventListener("click", () => {
            // Check if project and file are selected
            if (!this.selectedProject || !this.selectedFile) {
                alert("Please select a project and file first using the 'Select Project' button.");
                return;
            }
            
            // Get data from handler
            const data = handler();
            
            // Show loading state
            this.elements.saveToDatabaseBtn.disabled = true;
            this.elements.saveToDatabaseBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Saving...';
            
            // Send data to backend
            fetch("/save_to_database", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(result => {
                // Reset button state
                this.elements.saveToDatabaseBtn.disabled = false;
                this.elements.saveToDatabaseBtn.textContent = "Save to Database";
                
                if (result.error) {
                    alert(result.error);
                } else {
                    alert("Successfully saved to database!");
                }
            })
            .catch(err => {
                console.error("Error saving to database:", err);
                alert("An error occurred while saving to database.");
                this.elements.saveToDatabaseBtn.disabled = false;
                this.elements.saveToDatabaseBtn.textContent = "Save to Database";
            });
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
        this.elements.nextToFileSelectionBtn.disabled = false;
        this.selectedFile = null;
    }
    
    fetchProjects() {
        fetch("/get_projects")
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    this.populateProjectsDropdown(data.projects);
                }
            })
            .catch((err) => {
                console.error("Error fetching projects:", err);
                alert("An error occurred while fetching projects.");
            });
    }
    
    fetchFiles(projectName) {
        fetch(`/get_files?project_name=${encodeURIComponent(projectName)}`)
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    this.populateFilesDropdown(data.files);
                }
            })
            .catch((err) => {
                console.error("Error fetching files:", err);
                alert("An error occurred while fetching files.");
            });
    }
    
    populateProjectsDropdown(projects) {
        this.elements.existingProjects.innerHTML = '<option value="" disabled selected>Select a project</option>';
        projects.forEach((project) => {
            const option = document.createElement("option");
            option.value = project;
            option.textContent = project;
            this.elements.existingProjects.appendChild(option);
        });
    }
    
    populateFilesDropdown(files) {
        this.elements.projectFiles.innerHTML = '<option value="" disabled selected>Select a file</option>';
        files.forEach((file) => {
            const option = document.createElement("option");
            option.value = file;
            option.textContent = file;
            this.elements.projectFiles.appendChild(option);
        });
    }
    
    getProjectData() {
        // Use the selectedProject and selectedFile variables for accurate selection
        return {
            projectName: this.selectedProject,
            fileName: this.selectedFile
        };
    }

    // Add this method to the ProjectView class
    resetModalState() {
        // Reset modal to initial state
        this.elements.projectSelectionStep.classList.remove("d-none");
        this.elements.fileSelectionStep.classList.add("d-none");
        this.elements.confirmSelectionBtn.disabled = true;
        this.elements.newProjectName.value = "";
        this.elements.existingProjects.selectedIndex = 0;
        this.elements.projectFiles.innerHTML = '<option value="" disabled selected>Select a file</option>';
    }
}

/**
 * UML View - Modified to generate PlantUML from scenario text
 */
class UMLView {
    constructor() {
        this.elements = {
            plantumlText: document.getElementById("plantumlText"),
            scenarioText: document.getElementById("scenarioText")
        };
        
        this.displayDefaultPlantUML();
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
        this.elements.plantumlText.textContent = plantUML;
    }
    
    getScenarioText() {
        return this.elements.scenarioText.textContent.trim();
    }
    
    getPlantUMLText() {
        return this.elements.plantumlText.textContent.trim();
    }
}