// Global variables
window.saveTimeout = null;
const SAVE_DELAY = 1000; // 1 second delay
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

// Project save functionality
function markUnsavedChanges() {
    unsavedChanges = true;
    const saveButton = document.querySelector('.floating-save');
    if (saveButton) {
        saveButton.classList.add('btn-warning');
        saveButton.classList.remove('btn-primary');
    }
}

function markSavedChanges() {
    unsavedChanges = false;
    const saveButton = document.querySelector('.floating-save');
    if (saveButton) {
        saveButton.classList.remove('btn-warning');
        saveButton.classList.add('btn-primary');
    }
}

function autoSave() {
    clearTimeout(window.saveTimeout);
    markUnsavedChanges();
    window.saveTimeout = setTimeout(saveProject, SAVE_DELAY);
}

async function saveProject() {
    try {
        const formData = {
            icon: document.getElementById('project-icon').value,
            summary: document.getElementById('project-summary').value,
            description: document.getElementById('project-description').value,
            status: document.getElementById('project-status').value,
            priority: document.getElementById('project-priority').value,
            lead_id: document.getElementById('project-lead').value,
            team_members: Array.from(document.getElementById('project-team').selectedOptions).map(opt => opt.value),
            start_date: document.getElementById('project-start-date').value,
            end_date: document.getElementById('project-end-date').value,
            budget: document.getElementById('project-budget').value,
            category: document.getElementById('project-category').value,
            tags: document.getElementById('project-tags').value.split(',').map(tag => tag.trim()),
            visibility: document.getElementById('project-visibility').value,
            custom_fields: getCustomFields()
        };

        const response = await fetch(`/projects/${projectId}/update`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to save project changes');
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

// Custom fields handling
function getCustomFields() {
    const customFields = {};
    document.querySelectorAll('[data-custom-field]').forEach(field => {
        const fieldName = field.dataset.customField;
        const fieldType = field.dataset.fieldType;
        
        switch (fieldType) {
            case 'checkbox':
                customFields[fieldName] = field.checked;
                break;
            case 'date':
                customFields[fieldName] = field.value ? new Date(field.value).toISOString() : null;
                break;
            case 'number':
                customFields[fieldName] = field.value ? Number(field.value) : null;
                break;
            case 'select-multiple':
                customFields[fieldName] = Array.from(field.selectedOptions).map(opt => opt.value);
                break;
            default:
                customFields[fieldName] = field.value;
        }
    });
    return customFields;
}

// Icon functionality
function updateIconPreview() {
    const iconInput = document.getElementById('project-icon');
    const iconPreview = document.getElementById('icon-preview');
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
                                         onclick="selectIcon('${icon}')"
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
    document.getElementById('project-icon').value = iconClass;
    updateIconPreview();
    bootstrap.Modal.getInstance(document.getElementById('icon-picker-modal')).hide();
    autoSave();
}

// Team member management
async function searchUsers(query) {
    if (!query || query.length < 2) {
        document.getElementById('user-search-results').innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error('Failed to search users');
        }

        const users = await response.json();
        const resultsContainer = document.getElementById('user-search-results');
        
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
    try {
        const response = await fetch(`/projects/${projectId}/team/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (!response.ok) {
            throw new Error('Failed to add team member');
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

    try {
        const response = await fetch(`/projects/${projectId}/team/remove`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (!response.ok) {
            throw new Error('Failed to remove team member');
        }

        showSuccess('Team member removed successfully');
        location.reload(); // Refresh to show updated team
    } catch (error) {
        showError('Error removing team member: ' + error.message);
    }
}

async function promoteToLead(userId) {
    try {
        const response = await fetch(`/projects/${projectId}/lead`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (!response.ok) {
            throw new Error('Failed to update project lead');
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
    if (lastSavedElement) {
        lastSavedElement.textContent = new Date(timestamp).toLocaleString();
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize toastr
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000,
        preventDuplicates: true
    };
    
    // Add auto-save listeners to form fields
    const formFields = [
        'project-icon',
        'project-summary',
        'project-description',
        'project-status',
        'project-priority',
        'project-lead',
        'project-team',
        'project-start-date',
        'project-end-date',
        'project-budget',
        'project-category',
        'project-tags',
        'project-visibility'
    ];
    
    formFields.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (element) {
            element.addEventListener('change', autoSave);
            element.addEventListener('input', autoSave);
        }
    });
    
    // Add listeners to custom fields
    document.querySelectorAll('[data-custom-field]').forEach(field => {
        field.addEventListener('change', autoSave);
        field.addEventListener('input', autoSave);
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
    
    // Initialize select2 for tag input if available
    if ($.fn.select2) {
        $('#project-tags').select2({
            tags: true,
            tokenSeparators: [',', ' '],
            placeholder: 'Add tags...',
            theme: 'bootstrap-5'
        });
    }
    
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
});

// Export functions for use in other modules
window.projectModule = {
    saveProject,
    addTeamMember,
    removeTeamMember,
    promoteToLead,
    openIconPicker,
    updateIconPreview,
    searchUsers
};
