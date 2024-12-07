// Project module using IIFE to prevent global scope pollution
window.projectModule = (function() {
    // Private variables
    let unsavedChanges = false;

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
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }

    // Safe element getter
    function getElementValue(id, defaultValue = '') {
        const element = document.getElementById(id);
        if (!element) return defaultValue;
        return element.value ? element.value.trim() : defaultValue;
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
        
        // Get all form values
        const formData = {
            name: getElementValue('project-name'),
            icon: getElementValue('project-icon'),
            summary: getElementValue('project-summary'),
            description: description,
            status: getElementValue('project-status'),
            priority: getElementValue('project-priority'),
            lead_id: leadId ? parseInt(leadId) : null
        };

        // Log the form data for debugging
        console.log('Form data being sent:', formData);

        return formData;
    }

    async function createProject() {
        try {
            const formData = getProjectFormData();
            
            const response = await fetch('/projects/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to create project');
            }

            const result = await response.json();
            showSuccess('Project created successfully');
            // Redirect to the new project's page
            window.location.href = `/projects/${result.project_id}`;
        } catch (error) {
            showError('Error creating project: ' + error.message);
        }
    }

    async function saveProject() {
        if (!window.projectId) {
            showError('Project ID not found');
            return;
        }

        if (!unsavedChanges) {
            showInfo('No changes to save');
            return;
        }

        try {
            const formData = getProjectFormData();
            console.log('Saving project with data:', formData);

            const response = await fetch(`/projects/${window.projectId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to save project changes');
            }

            const result = await response.json();
            showSuccess('Project changes saved successfully');
            markSavedChanges();
            updateLastSaved(result.updated_at);
            updateIconPreview();
        } catch (error) {
            showError('Error saving project: ' + error.message);
        }
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

    // Team member management
    async function searchUsers(query) {
        if (!query || query.length < 2) {
            const resultsContainer = document.getElementById('user-search-results');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }
            return;
        }

        try {
            const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error('Failed to search users');
            }

            const users = await response.json();
            const resultsContainer = document.getElementById('user-search-results');
            if (!resultsContainer) return;
            
            if (users.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="list-group-item text-muted">
                        No users found matching "${query}"
                    </div>
                `;
                return;
            }

            resultsContainer.innerHTML = users
                .filter(user => !isTeamMember(user.id))
                .map(user => `
                    <div class="list-group-item user-search-item d-flex align-items-center" 
                         onclick="projectModule.addTeamMember(${user.id})">
                        <img src="${user.avatar_url}" alt="${user.name}" 
                             class="rounded-circle me-3" style="width: 32px; height: 32px;">
                        <div>
                            <h6 class="mb-0">${user.name}</h6>
                            <small class="text-muted">${user.email}</small>
                        </div>
                    </div>
                `).join('');
        } catch (error) {
            showError('Error searching users: ' + error.message);
        }
    }

    function isTeamMember(userId) {
        const teamMembers = Array.from(document.querySelectorAll('.team-member'))
            .map(el => parseInt(el.dataset.userId));
        return teamMembers.includes(userId);
    }

    async function addTeamMember(userId) {
        if (!window.projectId) {
            showError('Project ID not found');
            return;
        }

        try {
            const response = await fetch(`/projects/${window.projectId}/team/add`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': getCsrfToken()
                },
                body: JSON.stringify({ user_id: userId })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to add team member');
            }

            showSuccess('Team member added successfully');
            location.reload(); // Refresh to show new team member
        } catch (error) {
            showError('Error adding team member: ' + error.message);
        }
    }

    async function removeTeamMember(userId) {
        if (!confirm('Are you sure you want to remove this team member?')) {
            return;
        }

        if (!window.projectId) {
            showError('Project ID not found');
            return;
        }

        try {
            const response = await fetch(`/projects/${window.projectId}/team/remove`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': getCsrfToken()
                },
                body: JSON.stringify({ user_id: userId })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to remove team member');
            }

            showSuccess('Team member removed successfully');
            location.reload(); // Refresh to show updated team
        } catch (error) {
            showError('Error removing team member: ' + error.message);
        }
    }

    async function promoteToLead(userId) {
        if (!window.projectId) {
            showError('Project ID not found');
            return;
        }

        try {
            const response = await fetch(`/projects/${window.projectId}/lead`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': getCsrfToken()
                },
                body: JSON.stringify({ user_id: userId })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to update project lead');
            }

            showSuccess('Project lead updated successfully');
            location.reload(); // Refresh to show updated lead
        } catch (error) {
            showError('Error updating project lead: ' + error.message);
        }
    }

    // Project status updates
    function updateLastSaved(timestamp) {
        const lastSavedElement = document.getElementById('last-saved');
        if (lastSavedElement && timestamp) {
            lastSavedElement.textContent = new Date(timestamp).toLocaleString();
        }
    }

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize TinyMCE for project description
        const descriptionElement = document.getElementById('project-description');
        if (descriptionElement && !descriptionElement.hasAttribute('readonly')) {
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
        
        // Add change listeners to form fields
        const formFields = [
            'project-name',
            'project-icon',
            'project-summary',
            'project-status',
            'project-priority',
            'project-lead'
        ];
        
        formFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                // For select fields, only use change event
                if (element.tagName === 'SELECT') {
                    element.addEventListener('change', handleInputChange);
                } else {
                    // For other fields, use both change and input events
                    element.addEventListener('change', handleInputChange);
                    element.addEventListener('input', handleInputChange);
                }
            }
        });
        
        // Initialize icon preview
        updateIconPreview();
        
        // Add unsaved changes warning
        window.addEventListener('beforeunload', function(e) {
            if (unsavedChanges) {
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
        
        // Initialize user search
        const searchInput = document.getElementById('new-member-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    searchUsers(this.value);
                }, 300);
            });
        }

        // Initialize save buttons
        const saveButtons = document.querySelectorAll('.floating-save, .save-changes-btn');
        saveButtons.forEach(button => {
            button.innerHTML = `
                <i class="fas fa-save me-2"></i>
                <span class="save-text">Save Changes</span>
            `;
            button.addEventListener('click', saveProject);
        });
    });

    // Public API
    return {
        saveProject,
        createProject,
        addTeamMember,
        removeTeamMember,
        promoteToLead,
        openIconPicker,
        updateIconPreview,
        searchUsers,
        selectIcon
    };
})();
