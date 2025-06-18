// Listzy Main JavaScript

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize image previews
    initImagePreviews();
    
    // Initialize form validations
    initFormValidations();
    
    // Initialize auto-save (optional)
    // initAutoSave();
    
    console.log('🚀 Listzy initialized successfully');
}

// Tooltip initialization
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const element = event.target;
    const text = element.getAttribute('data-tooltip');
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #1f2937;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 14px;
        z-index: 9999;
        pointer-events: none;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    element._tooltip = tooltip;
}

function hideTooltip(event) {
    const element = event.target;
    if (element._tooltip) {
        document.body.removeChild(element._tooltip);
        delete element._tooltip;
    }
}

// Image preview functionality
function initImagePreviews() {
    const fileInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', handleImagePreview);
    });
}

function handleImagePreview(event) {
    const input = event.target;
    const file = input.files[0];
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            // Create or update preview
            let preview = input.parentNode.querySelector('.image-preview');
            if (!preview) {
                preview = document.createElement('img');
                preview.className = 'image-preview mt-2';
                input.parentNode.appendChild(preview);
            }
            preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

// Form validation enhancements
function initFormValidations() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearFieldError);
        });
    });
}

function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    
    // Clear previous errors
    clearFieldError({ target: field });
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Email validation
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(field, 'Please enter a valid email address');
            return false;
        }
    }
    
    // Price validation
    if (field.name === 'price' && value) {
        const price = parseFloat(value);
        if (isNaN(price) || price < 0) {
            showFieldError(field, 'Please enter a valid price');
            return false;
        }
    }
    
    return true;
}

function showFieldError(field, message) {
    const errorElement = document.createElement('p');
    errorElement.className = 'field-error text-red-600 text-sm mt-1';
    errorElement.textContent = message;
    
    field.classList.add('border-red-500');
    field.parentNode.appendChild(errorElement);
}

function clearFieldError(event) {
    const field = event.target;
    const existingError = field.parentNode.querySelector('.field-error');
    
    if (existingError) {
        existingError.remove();
        field.classList.remove('border-red-500');
    }
}

function handleFormSubmit(event) {
    const form = event.target;
    const fields = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    fields.forEach(field => {
        if (!validateField({ target: field })) {
            isValid = false;
        }
    });
    
    if (!isValid) {
        event.preventDefault();
        showToast('Please fix the errors above', 'error');
    }
}

// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="p-4">
            <div class="flex items-center">
                <div class="flex-1">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <button onclick="hideToast(this)" class="ml-4 text-gray-400 hover:text-gray-600">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto hide
    setTimeout(() => hideToast(toast), duration);
}

function hideToast(element) {
    const toast = element.closest ? element.closest('.toast') : element;
    toast.classList.remove('show');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// AJAX helper functions
function makeRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    return fetch(url, config)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showToast('Something went wrong. Please try again.', 'error');
            throw error;
        });
}

function getCSRFToken() {
    // Try multiple ways to get CSRF token
    let token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) {
        return token.value;
    }
    
    // Try getting from meta tag
    token = document.querySelector('meta[name="csrf-token"]');
    if (token) {
        return token.getAttribute('content');
    }
    
    // Try getting from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    
    return '';
}

// Product publishing functions
function publishToAllChannels(productId) {
    const button = event.target;
    const originalText = button.textContent;
    
    button.innerHTML = '<span class="spinner"></span>Publishing...';
    button.disabled = true;
    
    makeRequest(`/products/${productId}/publish-all/`, {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            
            // Show detailed results if available
            if (data.results) {
                setTimeout(() => {
                    showPublishingResults(data.results);
                }, 1000);
            }
            
            // Refresh page after short delay
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Publishing failed. Please try again.', 'error');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
}

function publishToChannel(productId, channelId) {
    const button = event.target;
    const originalText = button.textContent;
    
    button.innerHTML = '<span class="spinner"></span>Publishing...';
    button.disabled = true;
    
    makeRequest(`/products/${productId}/publish/${channelId}/`, {
        method: 'POST'
    })
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            
            // Update UI to show published status
            const statusElement = button.closest('.channel-item').querySelector('.status-indicator');
            if (statusElement) {
                statusElement.textContent = 'Published';
                statusElement.className = 'status-indicator status-active';
            }
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Publishing failed. Please try again.', 'error');
    })
    .finally(() => {
        button.textContent = originalText;
        button.disabled = false;
    });
}

function showPublishingResults(results) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 class="text-lg font-semibold mb-4">Publishing Results</h3>
            <div class="space-y-2">
                ${results.map(result => `
                    <div class="flex items-center justify-between p-2 rounded ${result.success ? 'bg-green-50' : 'bg-red-50'}">
                        <span class="font-medium">${result.channel}</span>
                        <span class="text-sm ${result.success ? 'text-green-600' : 'text-red-600'}">
                            ${result.success ? '✓ Success' : '✗ Failed'}
                        </span>
                    </div>
                `).join('')}
            </div>
            <button onclick="this.closest('.fixed').remove()" 
                    class="mt-4 w-full bg-blue-600 text-white px-4 py-2 rounded-lg">
                Close
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Utility functions
function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(price);
}

function formatDate(dateString) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(new Date(dateString));
}

function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Search functionality with debouncing
function initSearch() {
    const searchInput = document.querySelector('#search-input');
    if (searchInput) {
        const debouncedSearch = debounce(performSearch, 300);
        searchInput.addEventListener('input', debouncedSearch);
    }
}

function performSearch(event) {
    const query = event.target.value.trim();
    const searchForm = event.target.closest('form');
    
    if (query.length >= 2 || query.length === 0) {
        // Auto-submit form for search
        if (searchForm) {
            searchForm.submit();
        }
    }
}

// Analytics tracking (optional)
function trackEvent(eventName, properties = {}) {
    // Implement analytics tracking here
    console.log('Event tracked:', eventName, properties);
    
    // Example: Google Analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, properties);
    }
}

// Export functions for global access
window.ListzyApp = {
    showToast,
    hideToast,
    makeRequest,
    publishToAllChannels,
    publishToChannel,
    trackEvent,
    formatPrice,
    formatDate
};