// Comparison Page JavaScript

// State management
let availableResults = [];
let selectedResultIds = new Set();
let comparisonData = [];
let currentSortColumn = null;
let currentSortDirection = 'asc';

// DOM Elements
let resultsListContainer;
let compareBtn;
let selectAllBtn;
let deselectAllBtn;
let comparisonSection;
let comparisonTableBody;
let resultsSelectionContainer;
let loadingContainer;

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    loadAvailableResults();
    setupEventListeners();
});

// Initialize DOM elements
function initializeElements() {
    resultsListContainer = document.getElementById('results-list');
    compareBtn = document.getElementById('compare-btn');
    selectAllBtn = document.getElementById('select-all-btn');
    deselectAllBtn = document.getElementById('deselect-all-btn');
    comparisonSection = document.getElementById('comparison-section');
    comparisonTableBody = document.getElementById('comparison-table-body');
    resultsSelectionContainer = document.getElementById('results-selection-container');
    loadingContainer = document.getElementById('loading-container');
}

// Setup event listeners
function setupEventListeners() {
    selectAllBtn.addEventListener('click', () => {
        selectAllResults();
    });

    deselectAllBtn.addEventListener('click', () => {
        deselectAllResults();
    });

    compareBtn.addEventListener('click', () => {
        compareSelectedResults();
    });

    const newComparisonBtn = document.getElementById('new-comparison-btn');
    newComparisonBtn.addEventListener('click', () => {
        resetComparison();
    });

    const tableHeaders = document.querySelectorAll('.table-sortable th');
    tableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            if (column) {
                sortTable(column);
            }
        });
    });
}

// Load available evaluation results
async function loadAvailableResults() {
    try {
        loadingContainer.classList.remove('hidden');
        UIHelpers.clearMessages();

        const response = await API.evaluation.getResults();
        
        if (response.results && response.results.length > 0) {
            availableResults = response.results;
            renderResultsList();
        } else {
            resultsListContainer.innerHTML = `
                <div class="card-body">
                    <p class="text-secondary">No evaluation results available. Please complete an evaluation first.</p>
                    <a href="evaluation.html" class="btn btn-primary mt-2">Go to Evaluation</a>
                </div>
            `;
        }

        loadingContainer.classList.add('hidden');
        resultsSelectionContainer.classList.remove('hidden');

    } catch (error) {
        loadingContainer.classList.add('hidden');
        UIHelpers.handleAPIError(error);
    }
}

// Render results list with checkboxes
function renderResultsList() {
    if (availableResults.length === 0) {
        resultsListContainer.innerHTML = `
            <div class="card-body">
                <p class="text-secondary">No evaluation results available.</p>
            </div>
        `;
        return;
    }

    const listHTML = `
        <div class="card-body">
            <div class="list-group">
                ${availableResults.map(result => {
                    const resId = result.result_id || result.id;
                    return `
                    <div class="list-group-item">
                        <div class="form-check">
                            <input 
                                type="checkbox" 
                                class="form-check-input result-checkbox" 
                                id="result-${resId}" 
                                value="${resId}"
                                ${selectedResultIds.has(resId) ? 'checked' : ''}
                            >
                            <label class="form-check-label" for="result-${resId}">
                                <strong>${result.model_name}</strong>
                                <span class="text-secondary"> - ${UIHelpers.formatDate(result.date)}</span>
                                <br>
                                <small class="text-secondary">
                                    Accuracy: ${UIHelpers.formatNumber(result.metrics.accuracy * 100, 2)}% | 
                                    F1-Score: ${UIHelpers.formatNumber(result.metrics.f1_score * 100, 2)}%
                                </small>
                            </label>
                        </div>
                    </div>
                `;
                }).join('')}
            </div>
        </div>
    `;

    resultsListContainer.innerHTML = listHTML;

    const checkboxes = document.querySelectorAll('.result-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            handleCheckboxChange(e.target);
        });
    });

    updateCompareButtonState();
}

// Handle checkbox change
function handleCheckboxChange(checkbox) {
    const resultId = checkbox.value;
    
    if (checkbox.checked) {
        selectedResultIds.add(resultId);
    } else {
        selectedResultIds.delete(resultId);
    }

    updateCompareButtonState();
}

// Select all results
function selectAllResults() {
    selectedResultIds.clear();
    availableResults.forEach(result => {
        const resId = result.result_id || result.id;
        if (resId) {
            selectedResultIds.add(resId);
        }
    });
    
    const checkboxes = document.querySelectorAll('.result-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });

    updateCompareButtonState();
}

// Deselect all results
function deselectAllResults() {
    selectedResultIds.clear();
    
    const checkboxes = document.querySelectorAll('.result-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });

    updateCompareButtonState();
}

// Update compare button state
function updateCompareButtonState() {
    if (selectedResultIds.size >= 2) {
        compareBtn.disabled = false;
        compareBtn.textContent = `Compare Selected Results (${selectedResultIds.size})`;
    } else {
        compareBtn.disabled = true;
        compareBtn.textContent = 'Compare Selected Results (Select at least 2)';
    }
}

// Compare selected results
async function compareSelectedResults() {
    if (selectedResultIds.size < 2) {
        UIHelpers.showMessage('Please select at least 2 results to compare', 'warning');
        return;
    }

    try {
        compareBtn.disabled = true;
        compareBtn.innerHTML = '<span class="spinner spinner-sm"></span> Comparing...';
        UIHelpers.clearMessages();

        const resultIdsArray = Array.from(selectedResultIds);
        const response = await API.comparison.compare(resultIdsArray);

        if (response.comparison && response.comparison.length > 0) {
            comparisonData = response.comparison;
            displayComparisonTable();
            UIHelpers.showMessage('Comparison completed successfully', 'success');
        } else {
            UIHelpers.showMessage('No comparison data available', 'warning');
        }

    } catch (error) {
        UIHelpers.handleAPIError(error);
    } finally {
        compareBtn.disabled = false;
        compareBtn.textContent = `Compare Selected Results (${selectedResultIds.size})`;
    }
}

// Display comparison table
function displayComparisonTable() {
    if (comparisonData.length === 0) {
        return;
    }

    resultsSelectionContainer.classList.add('hidden');
    comparisonSection.classList.remove('hidden');

    renderTableRows();
    comparisonSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Render table rows
function renderTableRows() {
    const rowsHTML = comparisonData.map(result => `
        <tr>
            <td><strong>${result.model_name}</strong></td>
            <td>${UIHelpers.formatDate(result.date)}</td>
            <td>
                <span class="badge badge-${getMetricBadgeClass(result.metrics.accuracy)}">
                    ${UIHelpers.formatNumber(result.metrics.accuracy * 100, 2)}%
                </span>
            </td>
            <td>
                <span class="badge badge-${getMetricBadgeClass(result.metrics.precision)}">
                    ${UIHelpers.formatNumber(result.metrics.precision * 100, 2)}%
                </span>
            </td>
            <td>
                <span class="badge badge-${getMetricBadgeClass(result.metrics.recall)}">
                    ${UIHelpers.formatNumber(result.metrics.recall * 100, 2)}%
                </span>
            </td>
            <td>
                <span class="badge badge-${getMetricBadgeClass(result.metrics.f1_score)}">
                    ${UIHelpers.formatNumber(result.metrics.f1_score * 100, 2)}%
                </span>
            </td>
        </tr>
    `).join('');

    comparisonTableBody.innerHTML = rowsHTML;
}

// Get badge class based on metric value
function getMetricBadgeClass(value) {
    if (value >= 0.9) return 'success';
    if (value >= 0.7) return 'info';
    if (value >= 0.5) return 'warning';
    return 'danger';
}

// Sort table by column
function sortTable(column) {
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'asc';
    }

    comparisonData.sort((a, b) => {
        let valueA, valueB;

        if (column === 'model_name') {
            valueA = a.model_name.toLowerCase();
            valueB = b.model_name.toLowerCase();
        } else if (column === 'date') {
            valueA = String(a.date);
            valueB = String(b.date);
        } else {
            valueA = a.metrics[column];
            valueB = b.metrics[column];
        }

        if (valueA < valueB) {
            return currentSortDirection === 'asc' ? -1 : 1;
        }
        if (valueA > valueB) {
            return currentSortDirection === 'asc' ? 1 : -1;
        }
        return 0;
    });

    updateTableHeaders(column);
    renderTableRows();
}

// Update table headers with sort indicators
function updateTableHeaders(sortedColumn) {
    const headers = document.querySelectorAll('.table-sortable th');
    
    headers.forEach(header => {
        const column = header.dataset.column;
        header.classList.remove('sort-asc', 'sort-desc');
        if (column === sortedColumn) {
            header.classList.add(`sort-${currentSortDirection}`);
        }
    });
}

// Reset comparison
function resetComparison() {
    comparisonSection.classList.add('hidden');
    resultsSelectionContainer.classList.remove('hidden');
    
    comparisonData = [];
    currentSortColumn = null;
    currentSortDirection = 'asc';
    
    const headers = document.querySelectorAll('.table-sortable th');
    headers.forEach(header => {
        header.classList.remove('sort-asc', 'sort-desc');
    });
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
