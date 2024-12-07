// Get CSRF token from meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// Project functionality
function toggleTodo(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    const checkbox = document.getElementById(`todo-${id}`);
    if (!checkbox) {
        console.error('Todo checkbox not found');
        return;
    }

    fetch(`/projects/todo/${id}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
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

    const description = document.getElementById('todo-description')?.value?.trim();
    if (!description) {
        toastr.error('Todo description is required');
        return;
    }

    const assignedTo = document.getElementById('todo-assigned-to')?.value;

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
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            toastr.success('Todo created successfully');
            // Hide modal using Bootstrap 5 method
            const modal = bootstrap.Modal.getInstance(document.getElementById('add-todo-modal'));
            modal?.hide();
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

    if (!id) {
        console.error('Todo ID is required');
        return;
    }

    if (confirm('Are you sure you want to delete this todo?')) {
        fetch(`/projects/todo/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
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

    if (!Array.isArray(todos)) {
        console.error('Invalid todos array');
        return;
    }

    fetch('/projects/todo/reorder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ todos: todos })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
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

    const taskName = document.getElementById('task-name')?.value?.trim();
    if (!taskName) {
        toastr.error('Task name is required');
        return;
    }

    const formData = {
        name: taskName,
        description: document.getElementById('task-description')?.value?.trim() || '',
        status: document.getElementById('task-status')?.value || 'open',
        priority: document.getElementById('task-priority')?.value || 'medium',
        assigned_to_id: document.getElementById('task-assigned-to')?.value || null,
        due_date: document.getElementById('task-due-date')?.value || null
    };

    const taskId = document.getElementById('task-id')?.value;
    const method = taskId ? 'PUT' : 'POST';
    const url = taskId ? `/projects/task/${taskId}` : `/projects/${window.projectId}/task`;

    // Show loading state
    const submitButton = document.querySelector('#create-task-modal .btn-primary');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            toastr.success(`Task ${taskId ? 'updated' : 'created'} successfully`);
            // Hide modal using Bootstrap 5 method
            const modal = bootstrap.Modal.getInstance(document.getElementById('create-task-modal'));
            modal?.hide();
            location.reload();
        } else {
            throw new Error(data.message || `Failed to ${taskId ? 'update' : 'create'} task`);
        }
    })
    .catch(error => {
        console.error('Task operation error:', error);
        toastr.error(error.message || `An error occurred while ${taskId ? 'updating' : 'creating'} task`);
        // Reset button state
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    });
}

function viewTask(id) {
    if (!id) {
        console.error('Task ID is required');
        toastr.error('Invalid task ID');
        return;
    }

    currentTaskId = id;  // Store current task ID for edit button
    
    // Show loading state in modal
    const modal = new bootstrap.Modal(document.getElementById('view-task-modal'));
    modal.show();
    document.getElementById('view-task-name').textContent = 'Loading...';
    document.getElementById('view-task-description').innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x"></i></div>';
    
    fetch(`/projects/task/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.task) {
                const task = data.task;
                // Populate modal with task data
                document.getElementById('view-task-name').textContent = task.name || 'Unnamed Task';
                // Use rich-text-content class for proper HTML rendering
                document.getElementById('view-task-description').innerHTML = `<div class="rich-text-content">${task.description || 'No description provided'}</div>`;
                document.getElementById('view-task-status').innerHTML = `<span class="badge bg-${getStatusClass(task.status)}">${task.status}</span>`;
                document.getElementById('view-task-priority').innerHTML = `<span class="badge bg-${getPriorityClass(task.priority)}">${task.priority}</span>`;
                document.getElementById('view-task-assigned').textContent = task.assigned_to || 'Unassigned';
                document.getElementById('view-task-due-date').textContent = task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date';
                document.getElementById('view-task-created').textContent = task.created_at ? new Date(task.created_at).toLocaleString() : 'Unknown';
                document.getElementById('view-task-updated').textContent = task.updated_at ? new Date(task.updated_at).toLocaleString() : 'Unknown';

                // Populate task history
                const historyHtml = task.history?.map(entry => `
                    <tr>
                        <td>${new Date(entry.created_at).toLocaleString()}</td>
                        <td>${entry.user}</td>
                        <td><span class="badge bg-${entry.color}"><i class="fas fa-${entry.icon} me-1"></i>${entry.action}</span></td>
                        <td>${JSON.stringify(entry.details)}</td>
                    </tr>
                `).join('') || '<tr><td colspan="4" class="text-center">No history available</td></tr>';
                document.getElementById('view-task-history').innerHTML = historyHtml;

                // Populate task comments
                const commentsHtml = task.comments?.map(comment => `
                    <div class="direct-chat-msg ${comment.user_id === window.currentUserId ? 'right' : ''}">
                        <div class="direct-chat-infos clearfix">
                            <span class="direct-chat-name ${comment.user_id === window.currentUserId ? 'float-end' : 'float-start'}">
                                ${comment.user}
                            </span>
                            <span class="direct-chat-timestamp ${comment.user_id === window.currentUserId ? 'float-start' : 'float-end'}">
                                ${new Date(comment.created_at).toLocaleString()}
                            </span>
                        </div>
                        <img class="direct-chat-img" src="${comment.user_avatar || '/static/images/user_1.jpg'}" alt="User Image">
                        <div class="direct-chat-text">
                            ${comment.content}
                        </div>
                    </div>
                `).join('') || '<div class="text-center p-3">No comments yet</div>';
                document.getElementById('view-task-comments').innerHTML = commentsHtml;
            } else {
                throw new Error(data.message || 'Failed to load task');
            }
        })
        .catch(error => {
            console.error('Load task error:', error);
            document.getElementById('view-task-name').textContent = 'Error';
            document.getElementById('view-task-description').innerHTML = `<div class="alert alert-danger">Failed to load task: ${error.message}</div>`;
            toastr.error('An error occurred while loading task');
        });
}

function editTask(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    if (!id) {
        console.error('Task ID is required');
        toastr.error('Invalid task ID');
        return;
    }

    // Hide the view task modal if it's open
    const viewModal = bootstrap.Modal.getInstance(document.getElementById('view-task-modal'));
    if (viewModal) {
        viewModal.hide();
    }

    // Show loading state
    const editModal = new bootstrap.Modal(document.getElementById('create-task-modal'));
    editModal.show();
    document.querySelector('#create-task-modal .modal-title').textContent = 'Loading Task...';
    document.querySelector('#create-task-modal .modal-body').style.opacity = '0.5';

    fetch(`/projects/task/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.task) {
                const task = data.task;
                // Update modal title
                document.querySelector('#create-task-modal .modal-title').textContent = 'Edit Task';
                document.querySelector('#create-task-modal .modal-body').style.opacity = '1';
                
                // Populate form fields
                document.getElementById('task-id').value = task.id;
                document.getElementById('task-name').value = task.name || '';
                document.getElementById('task-description').value = task.description || '';
                document.getElementById('task-status').value = task.status || 'open';
                document.getElementById('task-priority').value = task.priority || 'medium';
                document.getElementById('task-assigned-to').value = task.assigned_to_id || '';
                document.getElementById('task-due-date').value = task.due_date || '';
                
                // Set created/updated timestamps
                document.getElementById('task-created').textContent = task.created_at ? new Date(task.created_at).toLocaleString() : 'Unknown';
                document.getElementById('task-updated').textContent = task.updated_at ? new Date(task.updated_at).toLocaleString() : 'Unknown';

                // Update submit button text
                document.querySelector('#create-task-modal .modal-footer .btn-primary').textContent = 'Save Changes';
            } else {
                throw new Error(data.message || 'Failed to load task');
            }
        })
        .catch(error => {
            console.error('Load task error:', error);
            toastr.error('An error occurred while loading task');
            // Reset modal
            document.querySelector('#create-task-modal .modal-title').textContent = 'Edit Task';
            document.querySelector('#create-task-modal .modal-body').style.opacity = '1';
            document.getElementById('task-form').reset();
        });
}

function deleteTask(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    if (!id) {
        console.error('Task ID is required');
        toastr.error('Invalid task ID');
        return;
    }

    if (confirm('Are you sure you want to delete this task?')) {
        fetch(`/projects/task/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                toastr.success('Task deleted successfully');
                location.reload();
            } else {
                throw new Error(data.message || 'Failed to delete task');
            }
        })
        .catch(error => {
            console.error('Delete task error:', error);
            toastr.error(error.message || 'An error occurred while deleting task');
        });
    }
}

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
    if (!saveButton) {
        console.error('Save button not found');
        return;
    }

    const originalContent = saveButton.innerHTML;
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveButton.disabled = true;

    // Get TinyMCE content
    const description = tinymce.get('description-editor')?.getContent() || '';

    // Collect all project data
    const projectData = {
        name: document.getElementById('project-name')?.value?.trim(),
        summary: document.getElementById('project-summary')?.value?.trim(),
        icon: document.getElementById('project-icon')?.value,
        description: description,
        lead_id: document.getElementById('lead-select')?.value,
        priority: document.getElementById('priority-select')?.options[document.getElementById('priority-select').selectedIndex]?.text,
        status: document.getElementById('status-select')?.options[document.getElementById('status-select').selectedIndex]?.text
    };

    // Validate required fields
    if (!projectData.name) {
        toastr.error('Project name is required');
        saveButton.innerHTML = originalContent;
        saveButton.disabled = false;
        return;
    }

    // Send update request
    fetch(`/projects/${window.projectId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(projectData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Reset button state
        saveButton.innerHTML = originalContent;
        saveButton.disabled = false;

        if (data.success) {
            toastr.success('Project saved successfully');
        } else {
            throw new Error(data.message || 'Failed to save project');
        }
    })
    .catch(error => {
        // Reset button state and show error
        saveButton.innerHTML = originalContent;
        saveButton.disabled = false;
        toastr.error(error.message || 'An error occurred while saving');
        console.error('Save error:', error);
    });
}

// Submit comment
function submitComment() {
    if (!window.canEdit) return false;

    const content = document.getElementById('comment-content')?.value?.trim();
    if (!content) {
        toastr.error('Comment content is required');
        return false;
    }

    fetch(`/projects/${window.projectId}/comment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            toastr.success('Comment added successfully');
            document.getElementById('comment-content').value = '';
            location.reload();
        } else {
            throw new Error(data.message || 'Failed to add comment');
        }
    })
    .catch(error => {
        console.error('Submit comment error:', error);
        toastr.error(error.message || 'An error occurred while adding comment');
    });

    return false;  // Prevent form submission
}

// Initialize todo list sorting when document is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.canEdit) {
        const todoList = document.querySelector('.todo-list');
        if (todoList) {
            new Sortable(todoList, {
                animation: 150,
                handle: '.todo-content',
                onEnd: function(evt) {
                    const todos = Array.from(todoList.children).map((item, index) => ({
                        id: parseInt(item.querySelector('input[type="checkbox"]').id.replace('todo-', '')),
                        order: index
                    }));
                    updateTodoOrder(todos);
                }
            });
        }
    }
});

// Reset create/edit task modal when closed
document.getElementById('create-task-modal')?.addEventListener('hidden.bs.modal', function () {
    // Reset form
    document.getElementById('task-form')?.reset();
    // Clear task ID
    document.getElementById('task-id').value = '';
    // Reset modal title
    document.querySelector('#create-task-modal .modal-title').textContent = 'Create Task';
    // Reset submit button text
    document.querySelector('#create-task-modal .modal-footer .btn-primary').textContent = 'Create Task';
    // Clear comments and history
    document.getElementById('task-comments').innerHTML = '';
    document.getElementById('task-history').innerHTML = '';
    // Clear timestamps
    document.getElementById('task-created').textContent = '';
    document.getElementById('task-updated').textContent = '';
    // Reset opacity
    document.querySelector('#create-task-modal .modal-body').style.opacity = '1';
});
