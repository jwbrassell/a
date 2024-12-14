// Project module using IIFE to prevent global scope pollution
window.projectModule = (function() {
    // Private variables
    let unsavedChanges = false;
    let intentionalNavigation = false;

    // Utility functions
    function showError(message) {
        toastr.error(message);
    }

    function showSuccess(message) {
        toastr.success(message);
    }

    function showWarning(message) {
        toastr.warning(message);
    }

    function showInfo(message) {
        toastr.info(message);
    }

    // Get CSRF token from meta tag
    function getCsrfToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!token) {
            console.error('CSRF token not found');
            return '';
        }
        return token;
    }

    // Safe element getter
    function getElementValue(id, defaultValue = '') {
        const element = document.getElementById(id);
        if (!element) return defaultValue;
        return element.value ? element.value.trim() : defaultValue;
    }

    // Get multiple select values
    function getMultiSelectValues(id) {
        const element = document.getElementById(id);
        if (!element) return [];
        return Array.from(element.selectedOptions).map(option => parseInt(option.value));
    }

    // Get multiple select text values (for roles)
    function getMultiSelectTextValues(id) {
        const element = document.getElementById(id);
        if (!element) return [];
        return Array.from(element.selectedOptions).map(option => option.value);
    }

    // Get todos from table
    function getTodos() {
        const todos = [];
        const todoRows = document.querySelectorAll('#todoList tr[data-todo-id]');
        todoRows.forEach((row, index) => {
            const todoId = row.dataset.todoId;
            const description = row.querySelector('.todo-text')?.textContent.trim();
            const completed = row.querySelector('.todo-checkbox')?.checked || false;
            const dueDateBadge = row.querySelector('.due-date-badge');
            const dueDate = dueDateBadge ? dueDateBadge.textContent.trim().split('\n').pop() : null;

            if (description) {
                todos.push({
                    id: todoId ? parseInt(todoId) : null,
                    description,
                    completed,
                    due_date: dueDate || null,
                    sort_order: index
                });
            }
        });
        return todos;
    }

    // Update header elements preview
    function updateHeaderPreview() {
        const headerName = document.getElementById('header-name');
        const headerIcon = document.getElementById('header-icon');
        const headerSummary = document.getElementById('header-summary');

        if (headerName) {
            headerName.textContent = getElementValue('project-name');
        }
        if (headerIcon) {
            headerIcon.className = getElementValue('project-icon') + ' me-2';
        }
        if (headerSummary) {
            headerSummary.textContent = getElementValue('project-summary');
        }
    }

    // Project save functionality
    function markUnsavedChanges() {
        if (!unsavedChanges) {
            unsavedChanges = true;
            // Update both floating save button and bottom save button
            const saveButtons = document.querySelectorAll('.floating-save, .save-changes-btn');
            saveButtons.forEach(button => {
                button.classList.add('btn-warning');
                button.classList.remove('btn-primary');
                const textSpan = button.querySelector('.save-text');
                if (textSpan) {
                    textSpan.textContent = 'Save Changes';
                }
            });
            showWarning('You have unsaved changes');
        }
    }

    function markSavedChanges() {
        unsavedChanges = false;
        // Update both floating save button and bottom save button
        const saveButtons = document.querySelectorAll('.floating-save, .save-changes-btn');
        saveButtons.forEach(button => {
            button.classList.remove('btn-warning');
            button.classList.add('btn-primary');
            const textSpan = button.querySelector('.save-text');
            if (textSpan) {
                textSpan.textContent = 'Save Changes';
            }
        });
    }

    function handleInputChange() {
        markUnsavedChanges();
        updateHeaderPreview();
    }

    function getProjectFormData() {
        // Get description from TinyMCE or fallback to textarea
        let description = '';
        const tinyMCEEditor = tinymce.get('project-description');
        const descriptionElement = document.getElementById('project-description');
        if (tinyMCEEditor) {
            description = tinyMCEEditor.getContent();
        } else if (descriptionElement) {
            description = descriptionElement.value || '';
        }

        // Get lead ID safely and ensure it's a number or null
        const leadId = getElementValue('project-lead');
        
        // Get private project status
        const isPrivate = document.getElementById('project-private')?.checked || false;

        // Get all form values
        const formData = {
            name: getElementValue('project-name'),
            icon: getElementValue('project-icon'),
            summary: getElementValue('project-summary'),
            description: description,
            status: getElementValue('project-status'),
            priority: getElementValue('project-priority'),
            lead_id: leadId ? parseInt(leadId) : null,
            watchers: getMultiSelectValues('project-watchers'),
            shareholders: getMultiSelectValues('project-shareholders'),
            stakeholders: getMultiSelectValues('project-stakeholders'),
            roles: getMultiSelectTextValues('project-role'),
            is_private: isPrivate,
            todos: getTodos()
        };

        return formData;
    }

    async function createProject(action = 'edit') {
        try {
            const formData = getProjectFormData();
            
            const response = await fetch('/projects/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            let errorMessage = 'Failed to create project';
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorMessage;
                } else {
                    const text = await response.text();
                    console.error('Server error:', text);
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            showSuccess('Project created successfully');
            markSavedChanges();

            // Set intentional navigation flag before redirect
            intentionalNavigation = true;

            // Redirect based on action
            if (action === 'edit') {
                window.location.href = `/projects/${result.project.id}/edit`;
            } else {
                window.location.href = '/projects/';  // Redirect to index page
            }
        } catch (error) {
            showError('Error creating project: ' + error.message);
        }
    }

    async function saveProject() {
        if (!window.projectId) {
            showError('Project ID not found');
            return;
        }

        try {
            const formData = getProjectFormData();

            const response = await fetch(`/projects/${window.projectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            let errorMessage = 'Failed to save project changes';
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorMessage;
                } else {
                    const text = await response.text();
                    console.error('Server error:', text);
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            showSuccess('Project changes saved successfully');
            markSavedChanges();
            
            // Update last saved timestamp if the element exists
            const lastSavedElement = document.getElementById('last-saved');
            if (lastSavedElement && result.project && result.project.updated_at) {
                lastSavedElement.textContent = new Date(result.project.updated_at).toLocaleString();
            }
            
            // Update Select2 fields with saved values
            if (result.project) {
                const project = result.project;
                
                // Update watchers
                if (project.watchers && project.watchers.length > 0) {
                    $('#project-watchers').val(project.watchers.map(w => w.id)).trigger('change');
                }
                
                // Update shareholders
                if (project.shareholders && project.shareholders.length > 0) {
                    $('#project-shareholders').val(project.shareholders.map(s => s.id)).trigger('change');
                }
                
                // Update stakeholders
                if (project.stakeholders && project.stakeholders.length > 0) {
                    $('#project-stakeholders').val(project.stakeholders.map(s => s.id)).trigger('change');
                }
                
                // Update roles
                if (project.roles && project.roles.length > 0) {
                    $('#project-role').val(project.roles.map(r => r.name)).trigger('change');
                }
            }
            
            updateIconPreview();

            // Reset all form change handlers
            resetFormChangeHandlers();
            
            // Set intentional navigation flag
            intentionalNavigation = true;
        } catch (error) {
            showError('Error saving project: ' + error.message);
            console.error('Save error:', error);
        }
    }

    async function deleteProject(projectId) {
        if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/projects/${projectId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCsrfToken()
                }
            });

            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                let errorMessage = 'Failed to delete project';
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorMessage;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            showSuccess('Project deleted successfully');
            
            // Redirect to projects index
            window.location.href = '/projects/';
        } catch (error) {
            showError('Error deleting project: ' + error.message);
        }
    }

    // Reset form change handlers
    function resetFormChangeHandlers() {
        // Remove and re-add all event listeners
        const formFields = [
            'project-name',
            'project-icon',
            'project-summary',
            'project-lead',
            'project-watchers',
            'project-shareholders',
            'project-stakeholders',
            'project-role',
            'project-private'
        ];

        formFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                const newElement = element.cloneNode(true);
                element.parentNode.replaceChild(newElement, element);

                if (newElement.type === 'checkbox') {
                    newElement.addEventListener('change', handleInputChange);
                } else {
                    newElement.addEventListener('change', handleInputChange);
                    newElement.addEventListener('input', handleInputChange);
                }
            }
        });

        // Reinitialize TinyMCE
        const descriptionElement = document.getElementById('project-description');
        if (descriptionElement && !descriptionElement.hasAttribute('readonly')) {
            if (tinymce.get('project-description')) {
                tinymce.get('project-description').remove();
            }
            initializeTinyMCE();
        }
    }

    // Initialize TinyMCE
    function initializeTinyMCE() {
        tinymce.init({
            selector: '#project-description',
            menubar: false,
            statusbar: false,
            branding: true,
            plugins: 'link image lists',
            toolbar: 'bold italic | bullist numlist | link image',
            height: 300,
            placeholder: 'Type your comment...',
            skin: document.querySelector('html').dataset.bsTheme === 'dark' ? 'oxide-dark' : 'oxide',
            content_css: document.querySelector('html').dataset.bsTheme === 'dark' ? 'dark' : 'default',
            setup: function(editor) {
                editor.on('change', function() {
                    editor.save();
                    handleInputChange();
                });
            },
            content_style: `
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    padding: 0.5rem;
                }
                p { margin: 0 0 1em 0; }
                img { max-width: 100%; height: auto; }
            `
        });
    }

    // Icon functionality
    function updateIconPreview() {
        const iconInput = document.getElementById('project-icon');
        const iconPreview = document.getElementById('icon-preview');
        if (!iconInput || !iconPreview) return;
        
        const newIcon = iconInput.value.trim();
        
        // Validate icon class
        if (!newIcon.match(/^[a-zA-Z0-9- ]+$/)) {
            showWarning('Invalid icon class format');
            return;
        }
        
        // Remove all existing classes and add the new one
        iconPreview.className = newIcon;
    }

    function openIconPicker() {
        // Create and show the icon picker modal
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'icon-picker-modal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'icon-picker-modal-label');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="icon-picker-modal-label">Select Icon</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <div class="input-group">
                                <span class="input-group-text">
                                    <i class="fas fa-search"></i>
                                </span>
                                <input type="text" class="form-control" id="icon-search" 
                                       placeholder="Search icons...">
                            </div>
                        </div>
                        <div class="row g-3" id="icon-grid">
                            <!-- Icons will be populated here -->
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Initialize the modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Load and display icons
        loadIcons();
        
        // Clean up when modal is hidden
        modal.addEventListener('hidden.bs.modal', function () {
            modal.remove();
        });
    }

    // Common Font Awesome icons categorized
    const iconCategories = {
        'Project Management': [
            'fas fa-project-diagram', 'fas fa-tasks', 'fas fa-clipboard-list',
            'fas fa-calendar-alt', 'fas fa-chart-bar', 'fas fa-kanban',
            'fas fa-list-check', 'fas fa-diagram-project', 'fas fa-timeline'
        ],
        'Development': [
            'fas fa-code', 'fas fa-bug', 'fas fa-terminal',
            'fas fa-laptop-code', 'fas fa-database', 'fas fa-code-branch',
            'fas fa-git', 'fas fa-microchip', 'fas fa-code-commit'
        ],
        'Business': [
            'fas fa-briefcase', 'fas fa-chart-line', 'fas fa-handshake',
            'fas fa-presentation', 'fas fa-calculator', 'fas fa-money-bill',
            'fas fa-file-contract', 'fas fa-building', 'fas fa-tie'
        ],
        'Communication': [
            'fas fa-comments', 'fas fa-envelope', 'fas fa-phone',
            'fas fa-video', 'fas fa-message', 'fas fa-share-nodes',
            'fas fa-bullhorn', 'fas fa-inbox', 'fas fa-paper-plane'
        ],
        'Design': [
            'fas fa-palette', 'fas fa-pencil', 'fas fa-paint-brush',
            'fas fa-vector-square', 'fas fa-crop', 'fas fa-wand-magic',
            'fas fa-swatchbook', 'fas fa-compass-drafting', 'fas fa-layers'
        ],
        'General': [
            'fas fa-folder', 'fas fa-star', 'fas fa-flag',
            'fas fa-bookmark', 'fas fa-heart', 'fas fa-circle-info',
            'fas fa-gear', 'fas fa-home', 'fas fa-lightbulb'
        ]
    };

    function loadIcons() {
        const grid = document.getElementById('icon-grid');
        const searchInput = document.getElementById('icon-search');
        
        if (!grid || !searchInput) return;
        
        function renderIcons(searchTerm = '') {
            grid.innerHTML = Object.entries(iconCategories)
                .map(([category, icons]) => {
                    const filteredIcons = searchTerm ? 
                        icons.filter(icon => icon.toLowerCase().includes(searchTerm.toLowerCase())) : 
                        icons;
                    
                    if (filteredIcons.length === 0) return '';
                    
                    return `
                        <div class="col-12">
                            <h6 class="border-bottom pb-2">${category}</h6>
                            <div class="row g-3 mb-4">
                                ${filteredIcons.map(icon => `
                                    <div class="col-md-2 col-sm-3 col-4">
                                        <div class="icon-option p-2 rounded text-center" 
                                             onclick="projectModule.selectIcon('${icon}')"
                                             role="button">
                                            <i class="${icon} fa-2x mb-2"></i>
                                            <br>
                                            <small class="text-muted">${icon.split(' ')[1]}</small>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }).join('');
        }
        
        // Initial render
        renderIcons();
        
        // Search functionality
        searchInput.addEventListener('input', function() {
            renderIcons(this.value);
        });
    }

    function selectIcon(iconClass) {
        const iconInput = document.getElementById('project-icon');
        if (!iconInput) return;
        
        iconInput.value = iconClass;
        updateIconPreview();
        const modal = document.getElementById('icon-picker-modal');
        if (modal) {
            bootstrap.Modal.getInstance(modal).hide();
        }
        handleInputChange();
    }

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize TinyMCE
        initializeTinyMCE();
        
        // Add change listeners to form fields
        const formFields = [
            'project-name',
            'project-icon',
            'project-summary',
            'project-lead',
            'project-watchers',
            'project-shareholders',
            'project-stakeholders',
            'project-role',
            'project-private'
        ];
        
        formFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                if (element.type === 'checkbox') {
                    element.addEventListener('change', handleInputChange);
                } else {
                    element.addEventListener('change', handleInputChange);
                    element.addEventListener('input', handleInputChange);
                }
            }
        });
        
        // Initialize icon preview
        updateIconPreview();
        
        // Add unsaved changes warning
        window.addEventListener('beforeunload', function(e) {
            if (unsavedChanges && !intentionalNavigation) {
                const message = 'You have unsaved changes. Are you sure you want to leave?';
                e.returnValue = message;
                return message;
            }
        });
        
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize save buttons
        const saveButtons = document.querySelectorAll('.floating-save, .save-changes-btn');
        saveButtons.forEach(button => {
            button.innerHTML = `
                <i class="fas fa-save me-2"></i>
                <span class="save-text">Save Changes</span>
            `;
            button.addEventListener('click', saveProject);
        });

        // Handle private project toggle
        $('#project-private').on('change', function() {
            const isPrivate = $(this).prop('checked');
            $('#public-project-sections').toggle(!isPrivate);
            handleInputChange();
        });
    });

    // Public API
    return {
        saveProject,
        createProject,
        deleteProject,
        openIconPicker,
        updateIconPreview,
        selectIcon,
        showError,
        showSuccess,
        showWarning,
        showInfo,
        getCsrfToken
    };
})();

// Make functions globally available
window.createProject = function(action) {
    projectModule.createProject(action);
};

window.deleteProject = function(projectId) {
    projectModule.deleteProject(projectId);
};
