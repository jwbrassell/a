// Template Plugin JavaScript

class TemplatePlugin {
    constructor() {
        this.initializeEventListeners();
        this.setupAjaxHandlers();
    }

    initializeEventListeners() {
        // Get Data button handler
        const getDataBtn = document.getElementById('getData');
        if (getDataBtn) {
            getDataBtn.addEventListener('click', (e) => this.handleGetData(e));
        }

        // Initialize tooltips
        this.initTooltips();
    }

    setupAjaxHandlers() {
        // Add CSRF token to all AJAX requests
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (csrfToken) {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRF-Token", csrfToken);
                    }
                }
            });
        }
    }

    initTooltips() {
        // Initialize Bootstrap tooltips
        $('[data-toggle="tooltip"]').tooltip();
    }

    async handleGetData(event) {
        const button = event.target;
        const resultContainer = document.getElementById('apiResult');

        try {
            // Show loading state
            this.setLoadingState(button, true);

            // Make API request
            const response = await fetch('/template/api/data', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Display result
            this.displayResult(resultContainer, data);

        } catch (error) {
            // Handle error
            this.displayError(resultContainer, error);
            console.error('API Error:', error);

        } finally {
            // Reset loading state
            this.setLoadingState(button, false);
        }
    }

    setLoadingState(button, isLoading) {
        if (isLoading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    displayResult(container, data) {
        container.innerHTML = `<pre class="json">${JSON.stringify(data, null, 2)}</pre>`;
        container.classList.remove('error');
        this.highlightJson(container);
    }

    displayError(container, error) {
        container.innerHTML = `<div class="alert alert-danger">
            <strong>Error:</strong> ${error.message}
        </div>`;
        container.classList.add('error');
    }

    highlightJson(container) {
        // Add syntax highlighting to JSON
        const pre = container.querySelector('pre.json');
        if (pre) {
            pre.innerHTML = pre.innerHTML
                .replace(/"([^"]+)":/g, '<span class="json-key">"$1":</span>')
                .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
                .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
                .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
                .replace(/: (null)/g, ': <span class="json-null">$1</span>');
        }
    }

    // Utility method for making API calls
    async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        if (data && method !== 'GET') {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }

        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    // Error handling utility
    handleError(error, container = null) {
        console.error('Plugin Error:', error);
        
        if (container) {
            this.displayError(container, error);
        }

        // Show error notification
        if (window.toastr) {
            toastr.error(error.message, 'Error');
        }
    }
}

// Initialize plugin when document is ready
document.addEventListener('DOMContentLoaded', () => {
    window.templatePlugin = new TemplatePlugin();
});

// Add custom event handlers
document.addEventListener('template:refresh', () => {
    if (window.templatePlugin) {
        const getDataBtn = document.getElementById('getData');
        if (getDataBtn) {
            getDataBtn.click();
        }
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemplatePlugin;
}
