// Utility functions
function showError(message) {
    toastr.error(message);
}

function showSuccess(message) {
    toastr.success(message);
}

function resetTodoForm() {
    document.getElementById('new-todo-form').reset();
    window.currentTodoId = null;
}

// Get CSRF token from meta tag
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Todo CRUD operations
async function createTodo() {
    try {
        const formData = {
            description: document.getElementById('todo-description').value,
            due_date: document.getElementById('todo-due-date').value,
            project_id: projectId
        };

        const response = await fetch('/projects/todos/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to create todo');
        }

        showSuccess('Todo created successfully');
        location.reload(); // Refresh to show new todo
    } catch (error) {
        showError('Error creating todo: ' + error.message);
    }
}

async function toggleTodo(todoId, completed) {
    try {
        const response = await fetch(`/projects/todos/${todoId}/toggle`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify({ completed })
        });

        if (!response.ok) {
            throw new Error('Failed to update todo status');
            // Revert checkbox state on error
            const checkbox = document.getElementById(`todoCheck${todoId}`);
            if (checkbox) {
                checkbox.checked = !completed;
            }
        }

        showSuccess('Todo status updated');
    } catch (error) {
        showError('Error updating todo: ' + error.message);
    }
}

async function editTodo(todoId) {
    try {
        const response = await fetch(`/projects/todos/${todoId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch todo details');
        }

        const todo = await response.json();
        window.currentTodoId = todoId;

        // Populate modal with todo details
        document.getElementById('todo-description').value = todo.description;
        document.getElementById('todo-due-date').value = todo.due_date;

        // Show modal
        $('#modal-new-todo').modal('show');
    } catch (error) {
        showError('Error editing todo: ' + error.message);
    }
}

async function updateTodo() {
    if (!window.currentTodoId) {
        showError('No todo selected for update');
        return;
    }

    try {
        const formData = {
            description: document.getElementById('todo-description').value,
            due_date: document.getElementById('todo-due-date').value
        };

        const response = await fetch(`/projects/todos/${window.currentTodoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to update todo');
        }

        showSuccess('Todo updated successfully');
        location.reload(); // Refresh to show updated todo
    } catch (error) {
        showError('Error updating todo: ' + error.message);
    }
}

async function deleteTodo(todoId) {
    if (!confirm('Are you sure you want to delete this todo item?')) {
        return;
    }

    try {
        const response = await fetch(`/projects/todos/${todoId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': getCsrfToken()
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete todo');
        }

        showSuccess('Todo deleted successfully');
        location.reload(); // Refresh to remove deleted todo
    } catch (error) {
        showError('Error deleting todo: ' + error.message);
    }
}

// Modal event handlers
function saveTodo() {
    if (window.currentTodoId) {
        updateTodo();
    } else {
        createTodo();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Reset form when modal is closed
    $('#modal-new-todo').on('hidden.bs.modal', function () {
        resetTodoForm();
    });

    // Initialize toastr if not already initialized
    if (typeof toastr !== 'undefined' && !toastr.options) {
        toastr.options = {
            closeButton: true,
            progressBar: true,
            positionClass: "toast-top-right",
            timeOut: 3000
        };
    }
});
