// Model Selection Page JavaScript

// DOM Elements
let apiKeyInput;
let modelNameInput;
let downloadBtn;
let showModelsBtn;
let downloadForm;
let loadingContainer;
let modelsSection;
let modelsList;

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    attachEventListeners();
    loadDownloadedModels();
});

// Initialize DOM elements
function initializeElements() {
    apiKeyInput = document.getElementById('api-key');
    modelNameInput = document.getElementById('model-name');
    downloadBtn = document.getElementById('download-btn');
    showModelsBtn = document.getElementById('show-models-btn');
    downloadForm = document.getElementById('model-download-form');
    loadingContainer = document.getElementById('loading-container');
    modelsSection = document.getElementById('models-section');
    modelsList = document.getElementById('models-list');
}

// Attach event listeners
function attachEventListeners() {
    downloadForm.addEventListener('submit', handleDownloadSubmit);
    showModelsBtn.addEventListener('click', toggleModelsSection);
    
    // Real-time validation
    apiKeyInput.addEventListener('input', () => validateApiKey(apiKeyInput.value));
    modelNameInput.addEventListener('input', () => validateModelName(modelNameInput.value));
}

// Handle form submission
async function handleDownloadSubmit(event) {
    event.preventDefault();
    
    // Clear previous messages
    UIHelpers.clearMessages();
    
    // Get form values
    const apiKey = apiKeyInput.value.trim();
    const modelName = modelNameInput.value.trim();
    
    // Validate inputs
    if (!validateApiKey(apiKey)) {
        UIHelpers.showMessage('Please enter a valid API key', 'error');
        return;
    }
    
    if (!validateModelName(modelName)) {
        UIHelpers.showMessage('Please enter a valid model name', 'error');
        return;
    }
    
    // Start download
    await downloadModel(apiKey, modelName);
}

// Validate API key
function validateApiKey(apiKey) {
    const result = UIHelpers.Validators.apiKey(apiKey);
    
    if (!result.valid) {
        UIHelpers.showValidationError(apiKeyInput, result.message);
        return false;
    }
    
    if (result.message) {
        // Show warning but still valid
        UIHelpers.showValidationSuccess(apiKeyInput, result.message);
    } else {
        UIHelpers.showValidationSuccess(apiKeyInput);
    }
    
    return true;
}

// Validate model name
function validateModelName(modelName) {
    const result = UIHelpers.Validators.modelName(modelName);
    
    if (!result.valid) {
        UIHelpers.showValidationError(modelNameInput, result.message);
        return false;
    }
    
    UIHelpers.showValidationSuccess(modelNameInput);
    return true;
}

// Download model from Hugging Face
async function downloadModel(apiKey, modelName) {
    try {
        // Show loading state with progress
        showLoadingState(modelName);
        
        // Show initial message
        UIHelpers.showMessage(
            `Downloading model "${modelName}"... This may take several minutes for large models (up to 30 minutes for 17GB+ models). Please be patient.`,
            'info',
            'message-container',
            false
        );
        
        // Call API (with 30 minute timeout)
        await API.model.downloadModel(apiKey, modelName);
        
        // Hide loading state
        hideLoadingState();
        
        // Clear info message
        UIHelpers.clearMessages();
        
        // Show success message
        UIHelpers.showMessage(
            `Model "${modelName}" downloaded successfully!`,
            'success'
        );
        
        // Clear form
        downloadForm.reset();
        apiKeyInput.classList.remove('is-valid');
        modelNameInput.classList.remove('is-valid');
        
        // Reload models list
        await loadDownloadedModels();
        
        // Show models section
        modelsSection.classList.remove('hidden');
        
    } catch (error) {
        // Hide loading state
        hideLoadingState();
        
        // Handle error
        UIHelpers.handleAPIError(error);
    }
}

// Show loading state
function showLoadingState(modelName = '') {
    // Disable form
    downloadBtn.disabled = true;
    apiKeyInput.disabled = true;
    modelNameInput.disabled = true;
    showModelsBtn.disabled = true;
    
    // Update loading container with model info
    loadingContainer.innerHTML = `
        <div class="loading-content" style="text-align: center; padding: 2rem;">
            <div class="spinner" style="margin: 0 auto 1rem;"></div>
            <h3 style="margin-bottom: 0.5rem;">Downloading Model</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">${modelName}</p>
            <div class="progress-info" style="font-size: 0.875rem; color: var(--text-secondary);">
                <p>⏳ Large models (10GB+) may take 15-30 minutes</p>
                <p>📦 Files are being downloaded from Hugging Face</p>
                <p>💾 Model will be cached locally for future use</p>
                <p style="margin-top: 1rem; font-weight: 500;">Please do not close this page...</p>
            </div>
            <div class="loading-animation" style="margin-top: 2rem;">
                <div class="pulse-dots">
                    <span style="animation-delay: 0s;">●</span>
                    <span style="animation-delay: 0.2s;">●</span>
                    <span style="animation-delay: 0.4s;">●</span>
                </div>
            </div>
        </div>
        <style>
            .pulse-dots {
                display: flex;
                justify-content: center;
                gap: 0.5rem;
                font-size: 1.5rem;
                color: var(--primary-color);
            }
            .pulse-dots span {
                animation: pulse 1.4s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 0.3; transform: scale(0.8); }
                50% { opacity: 1; transform: scale(1.2); }
            }
        </style>
    `;
    
    // Show loading container
    loadingContainer.classList.remove('hidden');
    
    // Scroll to loading container
    loadingContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Hide loading state
function hideLoadingState() {
    // Enable form
    downloadBtn.disabled = false;
    apiKeyInput.disabled = false;
    modelNameInput.disabled = false;
    showModelsBtn.disabled = false;
    
    // Hide loading container
    loadingContainer.classList.add('hidden');
}

// Load downloaded models
async function loadDownloadedModels() {
    try {
        const response = await API.model.getModels();
        
        if (response.models && response.models.length > 0) {
            displayModels(response.models);
        } else {
            displayNoModels();
        }
    } catch (error) {
        console.error('Error loading models:', error);
        displayNoModels();
    }
}

// Display models list
function displayModels(models) {
    modelsList.innerHTML = '';
    
    const listGroup = document.createElement('ul');
    listGroup.className = 'list-group';
    
    models.forEach(model => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item';
        listItem.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${model.name}</strong>
                    <br>
                    <small class="text-secondary">
                        Downloaded: ${UIHelpers.formatDate(model.download_date)}
                    </small>
                </div>
                <span class="badge badge-success">Ready</span>
            </div>
        `;
        listGroup.appendChild(listItem);
    });
    
    modelsList.appendChild(listGroup);
}

// Display no models message
function displayNoModels() {
    modelsList.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
            <p>No models downloaded yet.</p>
            <p>Download a model using the form above to get started.</p>
        </div>
    `;
}

// Toggle models section visibility
function toggleModelsSection() {
    if (modelsSection.classList.contains('hidden')) {
        modelsSection.classList.remove('hidden');
        showModelsBtn.textContent = 'Hide Downloaded Models';
        modelsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        modelsSection.classList.add('hidden');
        showModelsBtn.textContent = 'View Downloaded Models';
    }
}
