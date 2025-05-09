document.addEventListener("DOMContentLoaded", () => {
    // ============================
    // DOM Elements
    // ============================
    const userNameInput = document.getElementById("userName");
    const submitNameBtn = document.getElementById("submitNameBtn");
    const userInput = document.getElementById("userInput");
    const sendButton = document.getElementById("sendButton");
    const chatBox = document.getElementById("chatBox");
    const plantumlText = document.getElementById("plantumlText");
    const scenarioText = document.getElementById("scenarioText");
    const actionButtons = document.getElementById("actionButtons");
    const existingProjects = document.getElementById("existingProjects");
    const newProjectName = document.getElementById("newProjectName");
    const createProjectBtn = document.getElementById("createProjectBtn");
    const projectFiles = document.getElementById("projectFiles");
    const createFileBtn = document.getElementById("createFileBtn");
    const confirmSelectionBtn = document.getElementById("confirmSelectionBtn");
    const submitToDatabaseBtn = document.getElementById("submitToDatabaseBtn");

    // ============================
    // Initialization
    // ============================
    // Load saved name from sessionStorage
    const savedName = sessionStorage.getItem("userName");
    if (savedName) {
        userNameInput.value = savedName;
    }

    // Initialize default PlantUML
    displayDefaultPlantUML();

    // Fetch projects from the backend and populate the dropdown
    function fetchProjects() {
        fetch("/get_projects")
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    populateProjects(data.projects);
                }
            })
            .catch((err) => {
                console.error("Error fetching projects:", err);
                alert("An error occurred while fetching projects.");
            });
    }

    // Populate the projects dropdown
    function populateProjects(projects) {
        existingProjects.innerHTML = '<option value="" disabled selected>Select a project</option>';
        projects.forEach((project) => {
            const option = document.createElement("option");
            option.value = project;
            option.textContent = project;
            existingProjects.appendChild(option);
        });
    }

    // Call fetchProjects on page load
    fetchProjects();

    // Populate files for the selected project
    function populateFiles(projectName) {
        fetch(`/get_files?project_name=${encodeURIComponent(projectName)}`)
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    projectFiles.innerHTML = '<option value="" disabled selected>Select a file</option>';
                    data.files.forEach((file) => {
                        const option = document.createElement("option");
                        option.value = file;
                        option.textContent = file;
                        projectFiles.appendChild(option);
                    });
                }
            })
            .catch((err) => {
                console.error("Error fetching files:", err);
                alert("An error occurred while fetching files.");
            });
    }

    // ============================
    // Event Listeners
    // ============================
    submitNameBtn.addEventListener("click", handleNameSubmission);
    // Changed from sendMessage to providesInput to match activity diagram
    sendButton.addEventListener("click", providesInput);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            providesInput();
        }
    });
    
    createProjectBtn.addEventListener("click", () => {
        const projectName = newProjectName.value.trim();
        if (!projectName) {
            alert("Please enter a project name.");
            return;
        }

        // Send the project name to the backend
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
                    newProjectName.value = ""; // Clear the input field
                    fetchProjects(); // Refresh the projects dropdown
                }
            })
            .catch((err) => {
                console.error("Error creating project:", err);
                alert("An error occurred while creating the project.");
            });
    });

    // Event: Populate files when a project is selected
    existingProjects.addEventListener("change", (event) => {
        const selectedProject = event.target.value;
        populateFiles(selectedProject);
    });

    // Event: Create new file in the selected project
    createFileBtn.addEventListener("click", () => {
        const selectedProject = existingProjects.value;
        if (!selectedProject) {
            alert("Please select a project first.");
            return;
        }

        const fileName = prompt("Enter the file name:");
        if (!fileName) {
            alert("File name cannot be empty.");
            return;
        }

        // Send the file name and project name to the backend
        fetch("/create_file", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_name: selectedProject, file_name: fileName }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert("File created successfully!");
                    populateFiles(selectedProject); // Refresh the file list for the selected project
                }
            })
            .catch((err) => {
                console.error("Error creating file:", err);
                alert("An error occurred while creating the file.");
            });
    });

    // Event: Confirm selection
    confirmSelectionBtn.addEventListener("click", () => {
        const selectedProject = existingProjects.value;
        const selectedFile = projectFiles.value;
        if (!selectedProject || !selectedFile) {
            alert("Please select both a project and a file.");
            return;
        }
        alert(`Selected Project: ${selectedProject}, File: ${selectedFile}`);
        // Perform further actions with the selected project and file
    });

    submitToDatabaseBtn.addEventListener("click", () => {
        const projectName = existingProjects.value;
        const fileName = projectFiles.value;
        const username = sessionStorage.getItem("userName");
        
        // Check if scenario text is empty and convert to null if needed
        const scenarioRaw = scenarioText.textContent.trim();
        const scenario = scenarioRaw === "No detailed description provided." || 
                        scenarioRaw === "Your detailed scenario will be displayed here." ||
                        scenarioRaw === "" ? null : scenarioRaw;
        
        // Check if plantUML is empty and convert to null if needed
        const plantUMLRaw = plantumlText.textContent.trim();
        const plantUML = plantUMLRaw === "" ? null : plantUMLRaw;
        
        // Format chat history as direct array of objects with role and content
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

        // Validate project and file selection
        if (!projectName || !fileName) {
            alert("Please select a project and a file before submitting.");
            return;
        }

        // Prepare the payload to match the expected structure in MongoDB
        const payload = {
            project_name: projectName,
            file_name: fileName,
            username: username || "Anonymous",
            scenario: scenario,  // Will be null if empty
            plant_uml: plantUML, // Will be null if empty
            chat_history: chatHistory,
        };

        console.log("Submitting to database:", payload);

        // Send the data to the backend
        fetch("/submit_to_database", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert("Work result saved successfully!");
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while saving to the database.");
            });
    });

    // ============================
    // Core Functions - Renamed to match activity diagram
    // ============================

    // Handle name submission
    function handleNameSubmission() {
        const name = userNameInput.value.trim();
        if (!name) {
            alert("Please enter a name.");
            return;
        }

        sessionStorage.setItem("userName", name);

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

    // Renamed from sendMessage to providesInput to match activity diagram
    function providesInput() {
        const message = userInput.value.trim();
        if (!message) return;

        const userName = sessionStorage.getItem("userName");
        if (!userName) {
            alert("Please enter your name before starting the chat.");
            return;
        }

        // Display the user's message in the chatbox
        display_input(message);

        // Clear the input field and disable input while processing
        userInput.value = "";
        toggleInput(false); // Disable input and send button

        // Show loading indicator
        const loadingDiv = createLoadingIndicator();
        chatBox.appendChild(loadingDiv);
        autoScrollChatBox();

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
                loadingDiv.remove();

                if (data.error) {
                    displayErrorMessage(data.error); // Display error in the chatbox
                } else if (data.scenario) {
                    // Display scenario and summary
                    display_scenario(data.scenario);
                    display_response(data.summary);
                    showActionButtons();
                } else {
                    // General response
                    display_response(data.response || "No response provided.");
                }
            })
            .catch((err) => {
                loadingDiv.remove();
                displayErrorMessage("An error occurred while processing your request. Please try again.");
                console.error("Error:", err);
            })
            .finally(() => {
                toggleInput(true); // Re-enable input and send button
            });
    }

    // ============================
    // Helper Functions - Renamed to match activity diagram
    // ============================

    // Changed from appendMessage to display_input to match activity diagram
    function display_input(content) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", "user-message");
        messageDiv.textContent = content;
        chatBox.appendChild(messageDiv);
        autoScrollChatBox(); // Auto-scroll after appending the message
    }

    // Added to match activity diagram
    function display_scenario(scenario) {
        scenarioText.textContent = scenario || "No detailed description provided.";
    }

    // Changed from displayBotMessageWordByWord to display_response to match activity diagram
    function display_response(content) {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.classList.add("chat-message", "bot-message");
        
        // Render Markdown content using marked.js
        botMessageDiv.innerHTML = marked.parse(content);
        
        chatBox.appendChild(botMessageDiv);
        autoScrollChatBox(); // Auto-scroll after appending the message
    }

    // Toggle input and send button
    function toggleInput(enable) {
        userInput.disabled = !enable;
        sendButton.disabled = !enable;
        if (enable) userInput.focus();
    }

    // Create a loading indicator
    function createLoadingIndicator() {
        const loadingDiv = document.createElement("div");
        loadingDiv.classList.add("chat-message", "loading-message");
        loadingDiv.innerHTML = `
            <span class="loading-dots">
                <span></span><span></span><span></span>
            </span>`;
        return loadingDiv;
    }

    // Auto-scroll the chatbox
    function autoScrollChatBox() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Show action buttons
    function showActionButtons() {
        actionButtons.style.visibility = "visible";
        actionButtons.style.opacity = "1";
    }

    // Hide action buttons
    function hideActionButtons() {
        actionButtons.style.visibility = "hidden";
        actionButtons.style.opacity = "0";
    }

    // Display error messages
    function displayErrorMessage(errorText) {
        const errorDiv = document.createElement("div");
        errorDiv.classList.add("chat-message", "error-message");
        errorDiv.textContent = errorText;
        chatBox.appendChild(errorDiv);
        autoScrollChatBox();
    }

    // Display default PlantUML
    function displayDefaultPlantUML() {
        plantumlText.textContent = `@startuml
class User {
    +name: String
    +provides_input(): String
}

class Chatbot {
    +display_input(user_input): void
    +display_scenario(scenario): void
    +display_response(response): void
}

class LLMWrapper {
    +chat_history: List
    +determine_input_type(user_input): String
    +generate_response(user_name): String
    +generate_scenario(scenario_text): String
    +generate_summary(scenario): String
}
@enduml`;
    }

    // Generate UML button event
    document.getElementById("generateUMLBtn").addEventListener("click", function() {
        const scenario = scenarioText.textContent.trim();
        if (!scenario || scenario === "No detailed description provided.") {
            alert("Please generate a scenario first");
            return;
        }

        fetch("/generate_uml", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ scenarioText: scenario }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    plantumlText.textContent = data.plantuml;
                }
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("An error occurred while generating UML.");
            });
    });
});
