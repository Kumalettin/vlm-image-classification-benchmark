// API Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// API Error Class
class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

// Fetch wrapper with error handling and retry mechanism
async function fetchAPI(endpoint, options = {}, retryCount = 0) {
    const url = `${API_BASE_URL}${endpoint}`;
    const maxRetries = options.maxRetries || 2;
    const retryDelay = options.retryDelay || 1000;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 seconds default timeout
    };
    
    // Merge options
    const fetchOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    // Remove custom options that shouldn't be passed to fetch
    delete fetchOptions.maxRetries;
    delete fetchOptions.retryDelay;
    delete fetchOptions.timeout;
    
    // Remove Content-Type for FormData
    if (options.body instanceof FormData) {
        delete fetchOptions.headers['Content-Type'];
    }
    
    try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);
        fetchOptions.signal = controller.signal;
        
        const response = await fetch(url, fetchOptions);
        clearTimeout(timeoutId);
        
        // Parse response
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        
        // Handle errors
        if (!response.ok) {
            const errorMessage = data.message || data.error || `HTTP Error ${response.status}`;
            throw new APIError(errorMessage, response.status, data);
        }
        
        return data;
    } catch (error) {
        if (error instanceof APIError) {
            // Don't retry on client errors (4xx)
            if (error.status >= 400 && error.status < 500) {
                throw error;
            }
            
            // Retry on server errors (5xx) if retries available
            if (error.status >= 500 && retryCount < maxRetries) {
                console.log(`Retrying request (${retryCount + 1}/${maxRetries})...`);
                await sleep(retryDelay * (retryCount + 1)); // Exponential backoff
                return fetchAPI(endpoint, options, retryCount + 1);
            }
            
            throw error;
        }
        
        // Handle timeout
        if (error.name === 'AbortError') {
            throw new APIError('Request timeout. The server took too long to respond.', 0, null);
        }
        
        // Network or other errors
        if (error.name === 'TypeError' || error.message.includes('fetch') || error.message.includes('network')) {
            // Retry network errors if retries available
            if (retryCount < maxRetries) {
                console.log(`Network error, retrying (${retryCount + 1}/${maxRetries})...`);
                await sleep(retryDelay * (retryCount + 1));
                return fetchAPI(endpoint, options, retryCount + 1);
            }
            
            throw new APIError('Network error. Please check your connection and ensure the backend server is running.', 0, null);
        }
        
        throw new APIError(error.message || 'An unexpected error occurred', 0, null);
    }
}

// Sleep utility for retry delays
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// API Methods

// Model Management
const modelAPI = {
    // Download model from Hugging Face
    async downloadModel(apiKey, modelName) {
        return fetchAPI('/download-model', {
            method: 'POST',
            body: JSON.stringify({ api_key: apiKey, model_name: modelName }),
            timeout: 1800000, // 30 minutes timeout for large models
        });
    },
    
    // Get list of downloaded models
    async getModels() {
        return fetchAPI('/models', {
            method: 'GET',
        });
    },
};

// Classification
const classificationAPI = {
    // Start classification process
    async classify(modelId, folderPath, classes) {
        return fetchAPI('/classify', {
            method: 'POST',
            body: JSON.stringify({
                model_id: modelId,
                folder_path: folderPath,
                classes: classes,
            }),
        });
    },
    
    // Get classification status
    async getStatus(predictionId) {
        return fetchAPI(`/classification-status/${predictionId}`, {
            method: 'GET',
        });
    },
};

// Evaluation
const evaluationAPI = {
    // Get list of available predictions
    async getPredictions() {
        return fetchAPI('/predictions', {
            method: 'GET',
        });
    },
    
    // Upload ground truth file
    async uploadGroundTruth(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return fetchAPI('/upload-ground-truth', {
            method: 'POST',
            body: formData,
        });
    },
    
    // Evaluate model predictions
    async evaluate(predictionId, groundTruthPath, modelName = null) {
        return fetchAPI('/evaluate', {
            method: 'POST',
            body: JSON.stringify({
                prediction_id: predictionId,
                ground_truth_path: groundTruthPath,
                model_name: modelName,
            }),
        });
    },
    
    // Evaluate directly with prediction and ground truth data
    async evaluateDirect(predictionData, groundTruthData) {
        return fetchAPI('/evaluate-direct', {
            method: 'POST',
            body: JSON.stringify({
                predictions: predictionData.predictions,
                ground_truth: groundTruthData,
                model_name: predictionData.model_name || 'Unknown Model',
            }),
        });
    },
    
    // Get all evaluation results
    async getResults() {
        return fetchAPI('/results', {
            method: 'GET',
        });
    },
    
    // Get specific evaluation result
    async getResult(resultId) {
        return fetchAPI(`/result/${resultId}`, {
            method: 'GET',
        });
    },
};

// Comparison
const comparisonAPI = {
    // Compare multiple results
    async compare(resultIds) {
        return fetchAPI('/compare', {
            method: 'POST',
            body: JSON.stringify({ result_ids: resultIds }),
        });
    },
};

// UI Helper Functions

// Show loading spinner
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p class="loading-text">Loading...</p>
            </div>
        `;
        container.classList.remove('hidden');
    }
}

// Hide loading spinner
function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.classList.add('hidden');
    }
}

// Show message
function showMessage(message, type = 'info', containerId = 'message-container', autoHide = true) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ',
    };
    
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.innerHTML = `
        <span class="message-icon">${icons[type] || icons.info}</span>
        <div class="message-content">${message}</div>
        <button class="message-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(messageEl);
    container.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    if (autoHide) {
        setTimeout(() => {
            messageEl.remove();
            if (container.children.length === 0) {
                container.classList.add('hidden');
            }
        }, 5000);
    }
}

// Clear messages
function clearMessages(containerId = 'message-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
        container.classList.add('hidden');
    }
}

// Handle API errors
function handleAPIError(error, containerId = 'message-container') {
    console.error('API Error:', error);
    
    let errorMessage = 'An error occurred';
    
    if (error instanceof APIError) {
        errorMessage = error.message;
        
        if (error.status === 401) {
            errorMessage = 'Authentication failed. Please check your API key.';
        } else if (error.status === 404) {
            errorMessage = 'Resource not found. ' + error.message;
        } else if (error.status === 500) {
            errorMessage = 'Server error. ' + error.message;
        }
    } else {
        errorMessage = error.message || 'An unexpected error occurred';
    }
    
    showMessage(errorMessage, 'error', containerId, false);
}

// Update progress bar
function updateProgress(percentage, containerId = 'progress-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const progressBar = container.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${Math.round(percentage)}%`;
    }
}

// Format date (supports both ISO and YYYY-MM-DD_HH-MM-SS formats)
function formatDate(dateString) {
    if (!dateString) return '-';
    let normalized = String(dateString);
    if (/^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$/.test(normalized)) {
        const [d, t] = normalized.split('_');
        normalized = `${d}T${t.replace(/-/g, ':')}`;
    }
    const date = new Date(normalized);
    if (isNaN(date.getTime())) {
        return String(dateString);
    }
    return date.toLocaleString('tr-TR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });
}

// Format number with decimals
function formatNumber(number, decimals = 2) {
    return Number(number).toFixed(decimals);
}

// Validate form
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// Validation utilities
const Validators = {
    // Validate API key format
    apiKey(value) {
        if (!value || value.trim().length < 10) {
            return { valid: false, message: 'API key must be at least 10 characters' };
        }
        
        if (!value.trim().startsWith('hf_')) {
            return { valid: false, message: 'Hugging Face API keys must start with "hf_"' };
        }
        
        return { valid: true, message: '' };
    },
    
    // Validate model name format
    modelName(value) {
        if (!value || value.trim().length < 3) {
            return { valid: false, message: 'Model name must be at least 3 characters' };
        }
        
        if (!value.includes('/')) {
            return { valid: false, message: 'Model name should follow format: organization/model-name' };
        }
        
        if (!/^[a-zA-Z0-9_\-./]+$/.test(value)) {
            return { valid: false, message: 'Model name contains invalid characters' };
        }
        
        return { valid: true, message: '' };
    },
    
    // Validate folder path
    folderPath(value) {
        if (!value || value.trim().length === 0) {
            return { valid: false, message: 'Folder path is required' };
        }
        
        return { valid: true, message: '' };
    },
    
    // Validate class names
    classes(values) {
        if (!Array.isArray(values)) {
            return { valid: false, message: 'Classes must be an array' };
        }
        
        if (values.length < 2) {
            return { valid: false, message: 'At least 2 classes are required' };
        }
        
        if (values.length > 50) {
            return { valid: false, message: 'Maximum 50 classes allowed' };
        }
        
        const emptyIndex = values.findIndex(v => !v || v.trim().length === 0);
        if (emptyIndex !== -1) {
            return { valid: false, message: `Class ${emptyIndex + 1} cannot be empty` };
        }
        
        const lowerValues = values.map(v => v.toLowerCase());
        const uniqueValues = new Set(lowerValues);
        if (uniqueValues.size !== values.length) {
            return { valid: false, message: 'Duplicate class names are not allowed' };
        }
        
        return { valid: true, message: '' };
    },
    
    // Validate file upload
    file(file, allowedExtensions = ['.json'], maxSizeMB = 10) {
        if (!file) {
            return { valid: false, message: 'No file selected' };
        }
        
        const fileName = file.name.toLowerCase();
        const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
        
        if (!hasValidExtension) {
            return { 
                valid: false, 
                message: `Invalid file type. Allowed: ${allowedExtensions.join(', ')}` 
            };
        }
        
        const maxSizeBytes = maxSizeMB * 1024 * 1024;
        if (file.size > maxSizeBytes) {
            return { 
                valid: false, 
                message: `File too large. Maximum size: ${maxSizeMB}MB` 
            };
        }
        
        return { valid: true, message: '' };
    },
    
    // Validate number range
    numberRange(value, min, max) {
        const num = parseInt(value);
        
        if (isNaN(num)) {
            return { valid: false, message: 'Must be a valid number' };
        }
        
        if (num < min || num > max) {
            return { valid: false, message: `Must be between ${min} and ${max}` };
        }
        
        return { valid: true, message: '' };
    }
};

// Show validation error on input
function showValidationError(inputElement, message) {
    inputElement.classList.add('is-invalid');
    inputElement.classList.remove('is-valid');
    
    const existingError = inputElement.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    
    if (message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error';
        errorDiv.style.color = 'var(--error-color, #ef4444)';
        errorDiv.style.fontSize = '0.875rem';
        errorDiv.style.marginTop = '0.25rem';
        errorDiv.textContent = message;
        inputElement.parentElement.appendChild(errorDiv);
    }
}

// Show validation success on input
function showValidationSuccess(inputElement, message = '') {
    inputElement.classList.remove('is-invalid');
    inputElement.classList.add('is-valid');
    
    const existingError = inputElement.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    
    if (message) {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'validation-warning';
        warningDiv.style.color = 'var(--warning-color, #f59e0b)';
        warningDiv.style.fontSize = '0.875rem';
        warningDiv.style.marginTop = '0.25rem';
        warningDiv.textContent = message;
        inputElement.parentElement.appendChild(warningDiv);
    }
}

// Clear validation state
function clearValidation(inputElement) {
    inputElement.classList.remove('is-invalid', 'is-valid');
    
    const existingError = inputElement.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    
    const existingWarning = inputElement.parentElement.querySelector('.validation-warning');
    if (existingWarning) {
        existingWarning.remove();
    }
}

// Export API and helper functions
window.API = {
    model: modelAPI,
    classification: classificationAPI,
    evaluation: evaluationAPI,
    comparison: comparisonAPI,
};

window.UIHelpers = {
    showLoading,
    hideLoading,
    showMessage,
    clearMessages,
    handleAPIError,
    updateProgress,
    formatDate,
    formatNumber,
    validateForm,
    Validators,
    showValidationError,
    showValidationSuccess,
    clearValidation,
};
