// Utility functions for project management

// Toast notifications
export const notifications = {
    showError: (message) => {
        toastr.error(message);
    },
    showSuccess: (message) => {
        toastr.success(message);
    }
};

// Modal management
export const modal = {
    setLoading: (modalId, loading) => {
        const loadingOverlay = document.getElementById(`${modalId}-loading`);
        if (loadingOverlay) {
            loadingOverlay.classList.toggle('d-none', !loading);
        }
    },
    
    resetForm: (formId, editorId = null) => {
        document.getElementById(formId).reset();
        if (editorId) {
            const editor = tinymce.get(editorId);
            if (editor) {
                editor.setContent('');
                editor.getBody().contentEditable = true;
            }
        }
    },

    setupEditor: (editorId, modalId, options = {}) => {
        const defaultOptions = {
            menubar: false,
            plugins: 'lists link autolink paste',
            toolbar: 'bold italic | bullist numlist | link',
            height: 200,
            placeholder: 'Enter description...',
            paste_as_text: true,
            skin: document.querySelector('html').dataset.bsTheme === 'dark' ? 'oxide-dark' : 'oxide',
            content_css: document.querySelector('html').dataset.bsTheme === 'dark' ? 'dark' : 'default'
        };

        return tinymce.init({
            ...defaultOptions,
            ...options,
            selector: `#${editorId}`,
            setup: function(editor) {
                modal.setLoading(modalId, true);
                editor.on('init', function() {
                    modal.setLoading(modalId, false);
                    $(`#${modalId}`).on('shown.bs.modal', function() {
                        editor.focus();
                    });
                });
            }
        });
    }
};

// API helpers
export const api = {
    async fetchWithError(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`Request failed with status ${response.status}`);
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Operation failed');
            }

            return data;
        } catch (error) {
            notifications.showError(error.message);
            throw error;
        }
    }
};

// Form helpers
export const forms = {
    getFormData: (formId, editorId = null) => {
        const form = document.getElementById(formId);
        const formData = {};
        
        // Get regular form fields
        new FormData(form).forEach((value, key) => {
            formData[key] = value;
        });

        // Get editor content if specified
        if (editorId) {
            const editor = tinymce.get(editorId);
            if (editor) {
                formData.description = editor.getContent();
            }
        }

        return formData;
    },

    setFormData: (formId, data, editorId = null, disabled = false) => {
        const form = document.getElementById(formId);
        
        // Set form field values
        Object.entries(data).forEach(([key, value]) => {
            const field = form.elements[key];
            if (field) {
                field.value = value || '';
                field.disabled = disabled;
            }
        });

        // Set editor content if specified
        if (editorId) {
            const editor = tinymce.get(editorId);
            if (editor) {
                editor.setContent(data.description || '');
                editor.getBody().contentEditable = !disabled;
            }
        }
    }
};

// Initialize toastr settings
toastr.options = {
    closeButton: true,
    progressBar: true,
    positionClass: "toast-top-right",
    timeOut: 3000
};
