// Evaluation Page JavaScript

// State management
let state = {
    groundTruthData: null,
    predictionData: null,
    evaluationResult: null,
};

// DOM Elements
const elements = {
    groundTruthFile: null,
    groundTruthInfo: null,
    groundTruthDetails: null,
    predictionFile: null,
    predictionInfo: null,
    predictionDetails: null,
    evaluateBtn: null,
    loadingContainer: null,
    resultsSection: null,
    saveResultsBtn: null,
    metricAccuracy: null,
    metricPrecision: null,
    metricRecall: null,
    metricF1: null,
    confusionMatrixContainer: null,
    perClassMetricsContainer: null,
};

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    attachEventListeners();
});

// Initialize DOM elements
function initializeElements() {
    elements.groundTruthFile = document.getElementById('ground-truth-file');
    elements.groundTruthInfo = document.getElementById('ground-truth-info');
    elements.groundTruthDetails = document.getElementById('ground-truth-details');
    elements.predictionFile = document.getElementById('prediction-file');
    elements.predictionInfo = document.getElementById('prediction-info');
    elements.predictionDetails = document.getElementById('prediction-details');
    elements.evaluateBtn = document.getElementById('evaluate-btn');
    elements.loadingContainer = document.getElementById('loading-container');
    elements.resultsSection = document.getElementById('results-section');
    elements.saveResultsBtn = document.getElementById('save-results-btn');
    elements.metricAccuracy = document.getElementById('metric-accuracy');
    elements.metricPrecision = document.getElementById('metric-precision');
    elements.metricRecall = document.getElementById('metric-recall');
    elements.metricF1 = document.getElementById('metric-f1');
    elements.confusionMatrixContainer = document.getElementById('confusion-matrix-container');
    
    elements.perClassMetricsContainer = document.getElementById('per-class-metrics-container');
    
    // Debug: Check if elements are found
    console.log('🔍 Elements initialized:', {
        groundTruthFile: !!elements.groundTruthFile,
        predictionFile: !!elements.predictionFile,
        evaluateBtn: !!elements.evaluateBtn
    });
    
    if (!elements.predictionFile) {
        console.error('❌ prediction-file element not found!');
    }
}

// Attach event listeners
function attachEventListeners() {
    console.log('🔗 Attaching event listeners...');
    
    if (elements.groundTruthFile) {
        elements.groundTruthFile.addEventListener('change', handleGroundTruthUpload);
        console.log('✅ Ground truth file listener attached');
    } else {
        console.warn('⚠️ Ground truth file element not found');
    }
    
    if (elements.predictionFile) {
        elements.predictionFile.addEventListener('change', handlePredictionUpload);
        console.log('✅ Prediction file listener attached');
    } else {
        console.warn('⚠️ Prediction file element not found');
    }
    
    if (elements.evaluateBtn) {
        elements.evaluateBtn.addEventListener('click', handleEvaluate);
        console.log('✅ Evaluate button listener attached');
    } else {
        console.warn('⚠️ Evaluate button element not found');
    }
    
    if (elements.saveResultsBtn) {
        elements.saveResultsBtn.addEventListener('click', handleSaveResults);
        console.log('✅ Save results button listener attached');
    } else {
        console.warn('⚠️ Save results button element not found (this is OK if results section is hidden)');
    }
}

// Handle prediction file upload
async function handlePredictionUpload(event) {
    console.log('📁 Prediction file upload triggered');
    const file = event.target.files[0];
    
    if (!file) {
        console.log('❌ No file selected');
        return;
    }
    
    console.log('📄 File selected:', file.name);
    
    // Validate file
    const fileValidation = window.UIHelpers.Validators.file(file, ['.json'], 10);
    
    if (!fileValidation.valid) {
        console.log('❌ File validation failed:', fileValidation.message);
        window.UIHelpers.showMessage(fileValidation.message, 'error');
        event.target.value = '';
        return;
    }
    
    console.log('✅ File validation passed');
    
    try {
        // Read file content
        console.log('📖 Reading file content...');
        const fileContent = await readFileAsText(file);
        console.log('✅ File content read, length:', fileContent.length);
        
        const predictionData = JSON.parse(fileContent);
        console.log('✅ JSON parsed successfully');
        console.log('📊 Prediction data:', {
            has_predictions: !!predictionData.predictions,
            has_model_name: !!predictionData.model_name,
            prediction_count: predictionData.predictions ? Object.keys(predictionData.predictions).length : 0
        });
        
        // Validate prediction data structure
        if (!predictionData.predictions || !predictionData.model_name) {
            throw new Error('Invalid prediction file format. Must have "predictions" and "model_name" fields.');
        }
        
        // Store prediction data
        state.predictionData = predictionData;
        console.log('✅ Prediction data stored in state');
        
        // Show success info
        elements.predictionInfo.classList.remove('hidden');
        elements.predictionDetails.textContent = 
            `Model: ${predictionData.model_name}, Images: ${Object.keys(predictionData.predictions).length}`;
        
        console.log('✅ UI updated');
        
        // Update evaluate button state
        updateEvaluateButtonState();
        console.log('✅ Evaluate button state updated');
        
        window.UIHelpers.showMessage('Prediction file loaded successfully', 'success');
        
    } catch (error) {
        console.error('❌ Error loading prediction file:', error);
        window.UIHelpers.showMessage(
            `Failed to load prediction file: ${error.message}`,
            'error'
        );
        event.target.value = '';
        state.predictionData = null;
        elements.predictionInfo.classList.add('hidden');
    }
}

// Helper function to read file as text
function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

// Handle ground truth file upload
async function handleGroundTruthUpload(event) {
    const file = event.target.files[0];
    
    if (!file) {
        return;
    }
    
    // Validate file
    const fileValidation = window.UIHelpers.Validators.file(file, ['.json'], 10);
    
    if (!fileValidation.valid) {
        window.UIHelpers.showMessage(fileValidation.message, 'error');
        elements.groundTruthFile.value = '';
        return;
    }
    
    try {
        // Read and validate JSON file
        const fileContent = await readFileAsText(file);
        
        let groundTruthData;
        try {
            groundTruthData = JSON.parse(fileContent);
        } catch (parseError) {
            throw new Error('Invalid JSON format. Please check your file.');
        }
        
        // Validate structure
        if (typeof groundTruthData !== 'object' || Array.isArray(groundTruthData)) {
            throw new Error('Invalid ground truth format. Expected an object with image filenames as keys.');
        }
        
        const imageCount = Object.keys(groundTruthData).length;
        
        if (imageCount === 0) {
            throw new Error('Ground truth file is empty');
        }
        
        // Validate that all values are strings
        for (const [key, value] of Object.entries(groundTruthData)) {
            if (typeof value !== 'string') {
                throw new Error(`Invalid value for image "${key}". All class labels must be strings.`);
            }
        }
        
        // Store ground truth data
        state.groundTruthData = groundTruthData;
        
        elements.groundTruthInfo.classList.remove('hidden');
        elements.groundTruthDetails.textContent = `${imageCount} images loaded`;
        
        window.UIHelpers.showMessage('Ground truth file loaded successfully', 'success');
        
        // Update evaluate button state
        updateEvaluateButtonState();
        
    } catch (error) {
        window.UIHelpers.showMessage(`Error reading ground truth file: ${error.message}`, 'error');
        event.target.value = '';
        state.groundTruthData = null;
        elements.groundTruthInfo.classList.add('hidden');
    }
}

// Check if evaluate button should be enabled
function updateEvaluateButtonState() {
    const canEvaluate = state.groundTruthData && state.predictionData;
    elements.evaluateBtn.disabled = !canEvaluate;
}

// Alias for backward compatibility
function checkEvaluateButtonState() {
    updateEvaluateButtonState();
}

// Handle evaluate button click
async function handleEvaluate() {
    if (!state.groundTruthData || !state.predictionData) {
        window.UIHelpers.showMessage('Please upload both ground truth and prediction files', 'warning');
        return;
    }
    
    try {
        // Clear previous results
        elements.resultsSection.classList.add('hidden');
        window.UIHelpers.clearMessages();
        
        // Show loading
        window.UIHelpers.showLoading('loading-container');
        
        // Perform evaluation directly with the data
        const evaluationResult = await window.API.evaluation.evaluateDirect(
            state.predictionData,
            state.groundTruthData
        );
        
        // Store result
        state.evaluationResult = evaluationResult;
        
        // Hide loading
        window.UIHelpers.hideLoading('loading-container');
        
        // Display results
        displayEvaluationResults(evaluationResult);
        
        window.UIHelpers.showMessage('Evaluation completed successfully!', 'success');
        
    } catch (error) {
        window.UIHelpers.hideLoading('loading-container');
        window.UIHelpers.handleAPIError(error);
    }
}

// Display evaluation results
function displayEvaluationResults(result) {
    // Show results section
    elements.resultsSection.classList.remove('hidden');
    
    // Display metrics
    displayMetrics(result.metrics);
    
    // Display confusion matrix
    displayConfusionMatrix(result.confusion_matrix, result.classes);
    
    // Display per-class metrics
    displayPerClassMetrics(result.metrics.per_class_metrics, result.classes);
}

// Display main metrics
function displayMetrics(metrics) {
    elements.metricAccuracy.textContent = formatMetric(metrics.accuracy);
    elements.metricPrecision.textContent = formatMetric(metrics.precision);
    elements.metricRecall.textContent = formatMetric(metrics.recall);
    elements.metricF1.textContent = formatMetric(metrics.f1_score);
}

// Format metric value
function formatMetric(value) {
    return (value * 100).toFixed(1) + '%';
}

// Display confusion matrix
function displayConfusionMatrix(matrix, classes) {
    if (!matrix || !classes) {
        elements.confusionMatrixContainer.innerHTML = '<p class="text-secondary">No confusion matrix data available</p>';
        return;
    }
    
    // Create table
    let html = '<div class="table-container"><table class="table table-sm">';
    
    // Header row
    html += '<thead><tr><th>Actual \\ Predicted</th>';
    classes.forEach(cls => {
        html += `<th>${cls}</th>`;
    });
    html += '</tr></thead>';
    
    // Data rows
    html += '<tbody>';
    matrix.forEach((row, i) => {
        html += `<tr><th>${classes[i]}</th>`;
        row.forEach((value, j) => {
            // Highlight diagonal (correct predictions)
            const isCorrect = i === j;
            const bgColor = isCorrect ? 'background-color: rgba(16, 185, 129, 0.1);' : '';
            const fontWeight = isCorrect ? 'font-weight: 600;' : '';
            html += `<td style="${bgColor}${fontWeight}">${value}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    
    elements.confusionMatrixContainer.innerHTML = html;
}

// Display per-class metrics
function displayPerClassMetrics(perClassMetrics, classes) {
    if (!perClassMetrics || !classes) {
        elements.perClassMetricsContainer.innerHTML = '<p class="text-secondary">No per-class metrics available</p>';
        return;
    }
    
    // Create table
    let html = '<div class="table-container"><table class="table">';
    
    // Header
    html += `
        <thead>
            <tr>
                <th>Class</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1-Score</th>
            </tr>
        </thead>
    `;
    
    // Data rows
    html += '<tbody>';
    classes.forEach(cls => {
        const metrics = perClassMetrics[cls];
        if (metrics) {
            html += `
                <tr>
                    <td><strong>${cls}</strong></td>
                    <td>${formatMetric(metrics.precision)}</td>
                    <td>${formatMetric(metrics.recall)}</td>
                    <td>${formatMetric(metrics.f1)}</td>
                </tr>
            `;
        }
    });
    html += '</tbody></table></div>';
    
    elements.perClassMetricsContainer.innerHTML = html;
}

// Handle save results
async function handleSaveResults() {
    if (!state.evaluationResult) {
        window.UIHelpers.showMessage('No evaluation results to save', 'warning');
        return;
    }
    
    try {
        // Create a comprehensive results object
        const resultsToSave = {
            timestamp: new Date().toISOString(),
            model_name: state.predictionData.model_name,
            metrics: state.evaluationResult.metrics,
            confusion_matrix: state.evaluationResult.confusion_matrix,
            classes: state.evaluationResult.classes,
            matched_samples: state.evaluationResult.matched_samples,
            total_ground_truth: state.evaluationResult.total_ground_truth,
            total_predictions: state.evaluationResult.total_predictions
        };
        
        // Convert to JSON
        const jsonString = JSON.stringify(resultsToSave, null, 2);
        
        // Create blob and download
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        // Create download link
        const a = document.createElement('a');
        a.href = url;
        a.download = `evaluation_results_${state.predictionData.model_name.replace('/', '_')}_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        window.UIHelpers.showMessage('Results downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('Error saving results:', error);
        window.UIHelpers.showMessage(`Failed to save results: ${error.message}`, 'error');
    }
}
