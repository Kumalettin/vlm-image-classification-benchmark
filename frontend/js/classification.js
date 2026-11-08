// Classification page functionality

// State management
let selectedFolderPath = '';
let selectedModel = null;
let classNames = [];
let currentPredictionId = null;
let isFolderValid = false;

// DOM elements
const modelSelect = document.getElementById('modelSelect');
const folderPathInput = document.getElementById('folderPathInput');
const validateFolderButton = document.getElementById('validateFolderButton');
const folderInfo = document.getElementById('folderInfo');
const folderPath = document.getElementById('folderPath');
const folderStatus = document.getElementById('folderStatus');
const classCountInput = document.getElementById('classCount');
const classInputsContainer = document.getElementById('classInputsContainer');
const classInputs = document.getElementById('classInputs');
const startButton = document.getElementById('startButton');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const resultsContainer = document.getElementById('resultsContainer');
const predictionId = document.getElementById('predictionId');
const totalProcessed = document.getElementById('totalProcessed');
const newClassificationButton = document.getElementById('newClassificationButton');

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadModels();
    setupEventListeners();
});

// Load available models using shared API wrapper
async function loadModels() {
    try {
        const response = await window.API.model.getModels();
        
        if (response.models && response.models.length > 0) {
            modelSelect.innerHTML = '<option value="">Select a model...</option>';
            response.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.name} (${window.UIHelpers.formatDate(model.download_date)})`;
                modelSelect.appendChild(option);
            });
        } else {
            modelSelect.innerHTML = '<option value="">No models available</option>';
            window.UIHelpers.showMessage('No models found. Please download a model first.', 'warning');
        }
    } catch (error) {
        console.error('Error loading models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
        window.UIHelpers.handleAPIError(error);
    }
}

// Setup event listeners
function setupEventListeners() {
    modelSelect.addEventListener('change', handleModelChange);
    folderPathInput.addEventListener('input', handleFolderPathInput);
    validateFolderButton.addEventListener('click', validateFolder);
    classCountInput.addEventListener('input', handleClassCountChange);
    startButton.addEventListener('click', startClassification);
    newClassificationButton.addEventListener('click', resetForm);
}

// Handle model selection
function handleModelChange(e) {
    selectedModel = e.target.value;
    validateClassificationForm();
}

// Handle folder path input
function handleFolderPathInput() {
    isFolderValid = false;
    folderInfo.classList.add('hidden');
    validateClassificationForm();
}

// Validate folder path
async function validateFolder() {
    const path = folderPathInput.value.trim();
    const result = window.UIHelpers.Validators.folderPath(path);
    
    if (!result.valid) {
        window.UIHelpers.showMessage(result.message, 'error');
        return;
    }
    
    selectedFolderPath = path;
    isFolderValid = true;
    
    folderPath.textContent = path;
    folderStatus.textContent = 'Ready';
    folderStatus.className = 'badge badge-success';
    folderInfo.classList.remove('hidden');
    
    window.UIHelpers.showMessage('Folder path set. The backend will validate it when classification starts.', 'info');
    validateClassificationForm();
}

// Handle class count change (unified to 2-50 range)
function handleClassCountChange(e) {
    const count = parseInt(e.target.value);
    
    if (count >= 2 && count <= 50) {
        generateClassInputs(count);
        classInputsContainer.classList.remove('hidden');
    } else {
        classInputsContainer.classList.add('hidden');
    }
    
    validateClassificationForm();
}

// Generate dynamic class input fields
function generateClassInputs(count) {
    classInputs.innerHTML = '';
    
    for (let i = 0; i < count; i++) {
        const inputGroup = document.createElement('div');
        inputGroup.className = 'form-group';
        
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = `Class ${i + 1}`;
        
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-input';
        input.placeholder = `Enter class ${i + 1} name (e.g., cat, dog)`;
        input.dataset.classIndex = i;
        input.addEventListener('input', validateClassificationForm);
        
        inputGroup.appendChild(label);
        inputGroup.appendChild(input);
        classInputs.appendChild(inputGroup);
    }
}

// Collect class names from inputs
function getClassNames() {
    const inputs = classInputs.querySelectorAll('input');
    const names = [];
    
    inputs.forEach(input => {
        const value = input.value.trim();
        if (value) {
            names.push(value);
        }
    });
    
    return names;
}

// Validate form and enable/disable start button
function validateClassificationForm() {
    const count = parseInt(classCountInput.value);
    const names = getClassNames();
    
    const countResult = window.UIHelpers.Validators.numberRange(count, 2, 50);
    const classesResult = window.UIHelpers.Validators.classes(names);
    
    const isValid = 
        selectedModel &&
        isFolderValid &&
        countResult.valid &&
        classesResult.valid &&
        names.length === count;
    
    startButton.disabled = !isValid;
}

// Start classification process
async function startClassification() {
    try {
        startButton.disabled = true;
        modelSelect.disabled = true;
        folderPathInput.disabled = true;
        validateFolderButton.disabled = true;
        classCountInput.disabled = true;
        classInputs.querySelectorAll('input').forEach(input => input.disabled = true);
        
        classNames = getClassNames();
        
        progressContainer.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        updateClassificationProgress(0, 0);
        
        window.UIHelpers.showMessage('Starting classification...', 'info');
        
        const response = await window.API.classification.classify(
            selectedModel,
            selectedFolderPath,
            classNames
        );
        
        if (response.prediction_id) {
            currentPredictionId = response.prediction_id;
            await pollClassificationStatus(currentPredictionId);
        } else {
            throw new Error(response.message || 'Classification failed');
        }
        
    } catch (error) {
        console.error('Classification error:', error);
        window.UIHelpers.handleAPIError(error);
        
        startButton.disabled = false;
        modelSelect.disabled = false;
        folderPathInput.disabled = false;
        validateFolderButton.disabled = false;
        classCountInput.disabled = false;
        classInputs.querySelectorAll('input').forEach(input => input.disabled = false);
        
        progressContainer.classList.add('hidden');
    }
}

// Poll classification status
async function pollClassificationStatus(predId) {
    const pollInterval = 2000;
    
    const poll = async () => {
        try {
            const response = await window.API.classification.getStatus(predId);
            
            if (response.status === 'processing') {
                const current = response.progress?.current || 0;
                const total = response.progress?.total || 0;
                
                updateClassificationProgress(current, total);
                setTimeout(poll, pollInterval);
                
            } else if (response.status === 'completed') {
                const total = response.progress?.total || 0;
                updateClassificationProgress(total, total);
                showClassificationResults(predId, total);
                window.UIHelpers.showMessage('Classification completed successfully!', 'success');
                
            } else if (response.status === 'failed') {
                throw new Error(response.error || 'Classification failed');
            }
            
        } catch (error) {
            console.error('Status polling error:', error);
            window.UIHelpers.handleAPIError(error);
            
            startButton.disabled = false;
            modelSelect.disabled = false;
            folderPathInput.disabled = false;
            validateFolderButton.disabled = false;
            classCountInput.disabled = false;
            classInputs.querySelectorAll('input').forEach(input => input.disabled = false);
        }
    };
    
    poll();
}

// Update progress bar
function updateClassificationProgress(current, total) {
    const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
    
    progressBar.style.width = percentage + '%';
    progressBar.textContent = percentage + '%';
    progressText.textContent = `Processing images: ${current} / ${total}`;
}

// Show classification results
function showClassificationResults(predId, total) {
    predictionId.textContent = predId;
    totalProcessed.textContent = total;
    
    progressContainer.classList.add('hidden');
    resultsContainer.classList.remove('hidden');
}

// Reset form for new classification
function resetForm() {
    selectedFolderPath = '';
    selectedModel = null;
    classNames = [];
    currentPredictionId = null;
    isFolderValid = false;
    
    modelSelect.value = '';
    modelSelect.disabled = false;
    folderPathInput.value = '';
    folderPathInput.disabled = false;
    validateFolderButton.disabled = false;
    classCountInput.value = '';
    classCountInput.disabled = false;
    
    folderInfo.classList.add('hidden');
    classInputsContainer.classList.add('hidden');
    progressContainer.classList.add('hidden');
    resultsContainer.classList.add('hidden');
    
    window.UIHelpers.clearMessages();
    startButton.disabled = true;
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
