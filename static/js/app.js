// JavaScript functions for PedigreeDatabase
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            performSearch(this.value);
        }, 300));
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Health test type selection validation
    const testTypeSelect = document.getElementById('test_type_id');
    const resultInput = document.getElementById('result');
    
    if (testTypeSelect && resultInput) {
        testTypeSelect.addEventListener('change', function() {
            updateValidResults(this.value);
        });
    }
});

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search functionality
function performSearch(query) {
    if (query.length < 2) {
        return;
    }
    
    // Show loading spinner
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> Searching...</div>';
        
        // Simulate API call (replace with actual fetch when API search is implemented)
        setTimeout(() => {
            // This would be replaced with actual search results
            searchResults.innerHTML = '<div class="text-muted">Search functionality will be implemented with API endpoints.</div>';
        }, 500);
    }
}

// Update valid results based on test type
function updateValidResults(testTypeId) {
    const testTypes = window.testTypesData || {};
    const resultInput = document.getElementById('result');
    const resultHelp = document.getElementById('resultHelp');
    
    if (testTypeId && testTypes[testTypeId]) {
        const validResults = JSON.parse(testTypes[testTypeId]);
        if (resultHelp) {
            resultHelp.textContent = 'Valid results: ' + validResults.join(', ');
        }
        
        // Add datalist for autocomplete
        let datalist = document.getElementById('resultDatalist');
        if (!datalist) {
            datalist = document.createElement('datalist');
            datalist.id = 'resultDatalist';
            resultInput.parentNode.appendChild(datalist);
            resultInput.setAttribute('list', 'resultDatalist');
        }
        
        datalist.innerHTML = '';
        validResults.forEach(result => {
            const option = document.createElement('option');
            option.value = result;
            datalist.appendChild(option);
        });
    } else {
        if (resultHelp) {
            resultHelp.textContent = 'Valid results depend on the test type selected.';
        }
    }
}

// Confirm delete actions
function confirmDelete(itemName, deleteUrl) {
    if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
        window.location.href = deleteUrl;
    }
}

// Show success message
function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="bi bi-check-circle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Show error message
function showErrorMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 7 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 7000);
    }
}

// Format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Calculate age from birth date
function calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    return age;
}

// Export data functionality (placeholder)
function exportData(format) {
    alert(`Export to ${format} functionality will be implemented in future versions.`);
}

// Print pedigree
function printPedigree() {
    const printWindow = window.open('', '_blank');
    const pedigreeContent = document.querySelector('.pedigree-section');
    
    if (pedigreeContent) {
        printWindow.document.write(`
            <html>
                <head>
                    <title>Pedigree</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { padding: 20px; }
                        .pedigree-box { border: 1px solid #000; margin: 5px; padding: 10px; }
                    </style>
                </head>
                <body>
                    ${pedigreeContent.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}
