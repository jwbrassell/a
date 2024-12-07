// Get CSRF token from meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

// Project functionality
function toggleTodo(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    const checkbox = document.getElementById(`todo-${id}`);
    fetch(`/projects/todo/${id}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const todoText = checkbox.closest('.todo-item').querySelector('.todo-content');
            if (checkbox.checked) {
                todoText.classList.add('text-muted', 'text-decoration-line-through');
            } else {
                todoText.classList.remove('text-muted', 'text-decoration-line-through');
            }
            toastr.success('Todo status updated');
        } else {
            toastr.error(data.message || 'Failed to update todo');
        }
    })
    .catch(error => {
        console.error('Toggle todo error:', error);
        toastr.error('An error occurred while updating todo');
    });
}

function createTodo() {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    const description = document.getElementById('todo-description').value;
    const assignedTo = document.getElementById('todo-assigned-to').value;

    fetch(`/projects/${window.projectId}/todo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            description: description,
            assigned_to_id: assignedTo || null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastr.success('Todo created successfully');
            // Hide modal using Bootstrap 5 method
            const modal = bootstrap.Modal.getInstance(document.getElementById('add-todo-modal'));
            modal.hide();
            location.reload();
        } else {
            toastr.error(data.message || 'Failed to create todo');
        }
    })
    .catch(error => {
        console.error('Create todo error:', error);
        toastr.error('An error occurred while creating todo');
    });
}

function deleteTodo(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    if (confirm('Are you sure you want to delete this todo?')) {
        fetch(`/projects/todo/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastr.success('Todo deleted successfully');
                location.reload();
            } else {
                toastr.error(data.message || 'Failed to delete todo');
            }
        })
        .catch(error => {
            console.error('Delete todo error:', error);
            toastr.error('An error occurred while deleting todo');
        });
    }
}

function updateTodoOrder(todos) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    fetch('/projects/todo/reorder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ todos: todos })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to update todo order');
            toastr.error('Failed to update todo order');
        }
    })
    .catch(error => {
        console.error('Update todo order error:', error);
        toastr.error('An error occurred while updating todo order');
    });
}

function createTask() {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    const formData = {
        name: document.getElementById('task-name').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        assigned_to_id: document.getElementById('task-assigned-to').value || null,
        due_date: document.getElementById('task-due-date').value || null
    };

    const taskId = document.getElementById('task-id').value;
    const method = taskId ? 'PUT' : 'POST';
    const url = taskId ? `/projects/task/${taskId}` : `/projects/${window.projectId}/task`;

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastr.success(`Task ${taskId ? 'updated' : 'created'} successfully`);
            // Hide modal using Bootstrap 5 method
            const modal = bootstrap.Modal.getInstance(document.getElementById('create-task-modal'));
            modal.hide();
            location.reload();
        } else {
            toastr.error(data.message || `Failed to ${taskId ? 'update' : 'create'} task`);
        }
    })
    .catch(error => {
        console.error('Task operation error:', error);
        toastr.error(`An error occurred while ${taskId ? 'updating' : 'creating'} task`);
    });
}

function viewTask(id) {
    currentTaskId = id;  // Store current task ID for edit button
    fetch(`/projects/task/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const task = data.task;
                // Populate modal with task data
                document.getElementById('view-task-name').textContent = task.name;
                document.getElementById('view-task-description').innerHTML = task.description || 'No description provided';
                document.getElementById('view-task-status').innerHTML = `<span class="badge bg-${getStatusClass(task.status)}">${task.status}</span>`;
                document.getElementById('view-task-priority').innerHTML = `<span class="badge bg-${getPriorityClass(task.priority)}">${task.priority}</span>`;
                document.getElementById('view-task-assigned').textContent = task.assigned_to || 'Unassigned';
                document.getElementById('view-task-due-date').textContent = task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date';
                document.getElementById('view-task-created').textContent = new Date(task.created_at).toLocaleString();
                document.getElementById('view-task-updated').textContent = new Date(task.updated_at).toLocaleString();

                // Populate task history
                const historyHtml = task.history.map(entry => `
                    <tr>
                        <td>${new Date(entry.created_at).toLocaleString()}</td>
                        <td>${entry.user}</td>
                        <td><span class="badge bg-${entry.color}"><i class="fas fa-${entry.icon} me-1"></i>${entry.action}</span></td>
                        <td>${JSON.stringify(entry.details)}</td>
                    </tr>
                `).join('');
                document.getElementById('view-task-history').innerHTML = historyHtml;

                // Populate task comments
                const commentsHtml = task.comments.map(comment => `
                    <div class="direct-chat-msg ${comment.user_id === window.currentUserId ? 'right' : ''}">
                        <div class="direct-chat-infos clearfix">
                            <span class="direct-chat-name ${comment.user_id === window.currentUserId ? 'float-end' : 'float-start'}">
                                ${comment.user}
                            </span>
                            <span class="direct-chat-timestamp ${comment.user_id === window.currentUserId ? 'float-start' : 'float-end'}">
                                ${new Date(comment.created_at).toLocaleString()}
                            </span>
                        </div>
                        <img class="direct-chat-img" src="${comment.user_avatar}" alt="User Image">
                        <div class="direct-chat-text">
                            ${comment.content}
                        </div>
                    </div>
                `).join('');
                document.getElementById('view-task-comments').innerHTML = commentsHtml;
                
                // Show modal using Bootstrap 5 method
                const modal = new bootstrap.Modal(document.getElementById('view-task-modal'));
                modal.show();
            } else {
                toastr.error(data.message || 'Failed to load task');
            }
        })
        .catch(error => {
            console.error('Load task error:', error);
            toastr.error('An error occurred while loading task');
        });
}

function editTask(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    // Hide the view task modal if it's open
    const viewModal = bootstrap.Modal.getInstance(document.getElementById('view-task-modal'));
    if (viewModal) {
        viewModal.hide();
    }

    fetch(`/projects/task/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const task = data.task;
                // Update modal title
                document.querySelector('#create-task-modal .modal-title').textContent = 'Edit Task';
                
                // Populate modal with task data
                document.getElementById('task-id').value = task.id;
                document.getElementById('task-name').value = task.name;
                document.getElementById('task-description').value = task.description || '';
                document.getElementById('task-status').value = task.status;
                document.getElementById('task-priority').value = task.priority;
                document.getElementById('task-assigned-to').value = task.assigned_to_id || '';
                document.getElementById('task-due-date').value = task.due_date || '';
                
                // Update submit button text
                document.querySelector('#create-task-modal .modal-footer .btn-primary').textContent = 'Save Changes';
                
                // Show modal using Bootstrap 5 method
                const modal = new bootstrap.Modal(document.getElementById('create-task-modal'));
                modal.show();
            } else {
                toastr.error(data.message || 'Failed to load task');
            }
        })
        .catch(error => {
            console.error('Load task error:', error);
            toastr.error('An error occurred while loading task');
        });
}

function deleteTask(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    if (confirm('Are you sure you want to delete this task?')) {
        fetch(`/projects/task/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastr.success('Task deleted successfully');
                location.reload();
            } else {
                toastr.error(data.message || 'Failed to delete task');
            }
        })
        .catch(error => {
            console.error('Delete task error:', error);
            toastr.error('An error occurred while deleting task');
        });
    }
}

// Disable comment functionality
function submitComment() { return false; }
function submitTaskComment() { return false; }

// Helper functions for status and priority classes
function getStatusClass(status) {
    const statusClasses = {
        'open': 'secondary',
        'in_progress': 'primary',
        'review': 'info',
        'completed': 'success'
    };
    return statusClasses[status] || 'secondary';
}

function getPriorityClass(priority) {
    const priorityClasses = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger'
    };
    return priorityClasses[priority] || 'secondary';
}

// Save project changes
function saveProject() {
    if (!window.canEdit) return;

    // Show loading state
    const saveButton = document.querySelector('.floating-save-button');
    const originalContent = saveButton.innerHTML;
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveButton.disabled = true;

    // Get TinyMCE content
    const description = tinymce.get('description-editor').getContent();

    // Collect all project data
    const projectData = {
        name: document.getElementById('project-name').value,
        summary: document.getElementById('project-summary').value,
        icon: document.getElementById('project-icon').value,
        description: description,
        lead_id: document.getElementById('lead-select').value,
        priority: document.getElementById('priority-select').options[document.getElementById('priority-select').selectedIndex].text,
        status: document.getElementById('status-select').options[document.getElementById('status-select').selectedIndex].text
    };

    // Send update request
    fetch(`/projects/${window.projectId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(projectData)
    })
    .then(response => response.json())
    .then(data => {
        // Reset button state
        saveButton.innerHTML = originalContent;
        saveButton.disabled = false;

        if (data.success) {
            // Show success message
            toastr.success('Project saved successfully');
        } else {
            // Show error message
            toastr.error(data.message || 'Failed to save project');
        }
    })
    .catch(error => {
        // Reset button state and show error
        saveButton.innerHTML = originalContent;
        saveButton.disabled = false;
        toastr.error('An error occurred while saving');
        console.error('Save error:', error);
    });
}

// Icon picker functionality
const ICON_CATEGORIES = {
    'Solid': 'fas',
    'Regular': 'far',
    'Brands': 'fab'
};

function loadIcons() {
    const iconGrid = document.getElementById('icon-grid');
    iconGrid.innerHTML = ''; // Clear existing icons
    
    Object.entries(ICON_CATEGORIES).forEach(([category, prefix]) => {
        // Add category header
        const header = document.createElement('div');
        header.className = 'col-12 mt-3 mb-2';
        header.innerHTML = `<h5>${category}</h5>`;
        iconGrid.appendChild(header);

        // Add icons (this is a simplified list - you should load the full FA icon list)
        const commonIcons = [
            'project-diagram', 'tasks', 'clipboard-list', 'calendar', 'chart-line',
            'users', 'cog', 'bell', 'envelope', 'star', 'heart', 'bookmark',
            'file', 'folder', 'image', 'video', 'music', 'camera', 'phone',
            'home', 'building', 'car', 'plane', 'ship', 'truck', 'bicycle',
            'user', 'users', 'user-circle', 'user-plus', 'user-minus',
            'check', 'times', 'plus', 'minus', 'search', 'cog', 'wrench'
        ];

        commonIcons.forEach(icon => {
            const div = document.createElement('div');
            div.className = 'col-2 text-center mb-3';
            div.innerHTML = `
                <div class="icon-option p-2" data-icon="${prefix} fa-${icon}">
                    <i class="${prefix} fa-${icon} fa-2x"></i>
                    <div class="small text-muted mt-1">${icon}</div>
                </div>
            `;
            
            // Add click handler directly to the icon option
            const iconOption = div.querySelector('.icon-option');
            iconOption.addEventListener('click', function() {
                // Remove selection from other icons
                document.querySelectorAll('.icon-option.selected').forEach(el => {
                    el.classList.remove('selected');
                });
                // Add selection to clicked icon
                this.classList.add('selected');
            });
            
            iconGrid.appendChild(div);
        });
    });
}

// Initialize icon picker when modal is shown
document.getElementById('icon-picker-modal')?.addEventListener('show.bs.modal', function () {
    loadIcons();
});

// Icon search functionality
const iconSearchInput = document.getElementById('icon-search');
if (iconSearchInput) {
    iconSearchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        document.querySelectorAll('#icon-grid .icon-option').forEach(option => {
            const iconName = option.dataset.icon.toLowerCase();
            option.closest('.col-2').style.display = 
                iconName.includes(searchTerm) ? 'block' : 'none';
        });
    });
}

// Save selected icon
function saveSelectedIcon() {
    const selectedIcon = document.querySelector('#icon-grid .icon-option.selected');
    if (selectedIcon) {
        document.getElementById('project-icon').value = selectedIcon.dataset.icon;
        // Update the preview icon
        const previewIcon = document.querySelector('.input-group-text i');
        previewIcon.className = selectedIcon.dataset.icon;
        // Hide modal using Bootstrap 5 method
        const modal = bootstrap.Modal.getInstance(document.getElementById('icon-picker-modal'));
        modal.hide();
        toastr.success('Icon selected');
    }
}

// Reset create/edit task modal when closed
document.getElementById('create-task-modal')?.addEventListener('hidden.bs.modal', function () {
    // Reset form
    document.getElementById('task-form').reset();
    // Clear task ID
    document.getElementById('task-id').value = '';
    // Reset modal title
    document.querySelector('#create-task-modal .modal-title').textContent = 'Create Task';
    // Reset submit button text
    document.querySelector('#create-task-modal .modal-footer .btn-primary').textContent = 'Create Task';
});
