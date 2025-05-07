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
    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
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
        const scenario = scenarioText.textContent.trim();
        const plantUML = plantumlText.textContent.trim();
        const chatHistory = Array.from(document.querySelectorAll(".chat-message")).map(
            (msg) => msg.textContent.trim()
        );

        // Validate project and file selection
        if (!projectName || !fileName) {
            alert("Please select a project and a file before submitting.");
            return;
        }

        // Prepare the payload
        const payload = {
            project_name: projectName,
            file_name: fileName,
            username: username || "Anonymous", // Default to "Anonymous" if no username is set
            scenario: scenario,
            plant_uml: plantUML,
            chat_history: chatHistory,
        };

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
    // Core Functions
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

    // Send a message
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        const userName = sessionStorage.getItem("userName");
        if (!userName) {
            alert("Please enter your name before starting the chat.");
            return;
        }

        // Display the user's message in the chatbox
        appendMessage("user", message);

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
                    scenarioText.textContent = data.scenario || "No detailed description provided.";
                    displayBotMessageWordByWord(data.summary, showActionButtons);
                } else {
                    // General response
                    displayBotMessageWordByWord(data.response || "No response provided.");
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
    // Helper Functions
    // ============================

    // Append a message to the chatbox
    function appendMessage(role, content) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", `${role}-message`);

        // Render Markdown content using marked.js
        if (role === "bot") {
            messageDiv.innerHTML = marked.parse(content); // Convert Markdown to HTML
        } else {
            messageDiv.textContent = content; // Plain text for user messages
        }

        chatBox.appendChild(messageDiv);
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

    // Display bot messages word by word
    function displayBotMessageWordByWord(text, callback) {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.classList.add("chat-message", "bot-message");
        chatBox.appendChild(botMessageDiv);

        const words = text.split(" ");
        let index = 0;

        function displayNextWord() {
            if (index < words.length) {
                botMessageDiv.textContent += words[index] + " ";
                index++;
                autoScrollChatBox(); // Auto-scroll after adding each word
                setTimeout(displayNextWord, 30); // Adjust delay as needed
            } else {
                // Render Markdown after the full response is displayed
                botMessageDiv.innerHTML = marked.parse(botMessageDiv.textContent);
                if (callback) {
                    callback();
                }
            }
        }

        displayNextWord();
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
    +email: String
    +login(): void
}

class Product {
    +id: int
    +name: String
    +price: float
}

User "1" -- "0..*" Product : purchases
@enduml`;
    }
});
