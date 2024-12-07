// Global variables
let currentTaskId = null;

// Utility functions
function showError(message) {
    toastr.error(message);
}

function showSuccess(message) {
    toastr.success(message);
}

function resetTaskForm() {
    document.getElementById('new-task-form').reset();
    currentTaskId = null;
}

// Task CRUD operations
async function createTask() {
    try {
        const formData = {
            name: document.getElementById('task-name').value,
            assigned_to: document.getElementById('task-assigned').value,
            status: document.getElementById('task-status').value,
            priority: document.getElementById('task-priority').value,
            due_date: document.getElementById('task-due-date').value,
            project_id: projectId
        };

        const response = await fetch('/projects/tasks/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to create task');
        }

        const result = await response.json();
        showSuccess('Task created successfully');
        location.reload(); // Refresh to show new task
    } catch (error) {
        showError('Error creating task: ' + error.message);
    }
}

async function viewTask(taskId) {
    try {
        const response = await fetch(`/projects/tasks/${taskId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch task details');
        }

        const task = await response.json();
        // Populate modal with task details
        document.getElementById('task-name').value = task.name;
        document.getElementById('task-assigned').value = task.assigned_to || '';
        document.getElementById('task-status').value = task.status;
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-due-date').value = task.due_date;

        // Update modal for viewing
        document.querySelectorAll('#new-task-form input, #new-task-form select').forEach(el => {
            el.disabled = true;
        });
        
        $('#modal-new-task').modal('show');
    } catch (error) {
        showError('Error viewing task: ' + error.message);
    }
}

async function editTask(taskId) {
    try {
        const response = await fetch(`/projects/tasks/${taskId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch task details');
        }

        const task = await response.json();
        currentTaskId = taskId;

        // Populate modal with task details
        document.getElementById('task-name').value = task.name;
        document.getElementById('task-assigned').value = task.assigned_to || '';
        document.getElementById('task-status').value = task.status;
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-due-date').value = task.due_date;

        // Enable form fields for editing
        document.querySelectorAll('#new-task-form input, #new-task-form select').forEach(el => {
            el.disabled = false;
        });

        $('#modal-new-task').modal('show');
    } catch (error) {
        showError('Error editing task: ' + error.message);
    }
}

async function updateTask() {
    if (!currentTaskId) {
        showError('No task selected for update');
        return;
    }

    try {
        const formData = {
            name: document.getElementById('task-name').value,
            assigned_to: document.getElementById('task-assigned').value,
            status: document.getElementById('task-status').value,
            priority: document.getElementById('task-priority').value,
            due_date: document.getElementById('task-due-date').value
        };

        const response = await fetch(`/projects/tasks/${currentTaskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to update task');
        }

        showSuccess('Task updated successfully');
        location.reload(); // Refresh to show updated task
    } catch (error) {
        showError('Error updating task: ' + error.message);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    try {
        const response = await fetch(`/projects/tasks/${taskId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete task');
        }

        showSuccess('Task deleted successfully');
        location.reload(); // Refresh to remove deleted task
    } catch (error) {
        showError('Error deleting task: ' + error.message);
    }
}

// Modal event handlers
function saveNewTask() {
    if (currentTaskId) {
        updateTask();
    } else {
        createTask();
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Reset form when modal is closed
    $('#modal-new-task').on('hidden.bs.modal', function () {
        resetTaskForm();
    });

    // Initialize toastr
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000
    };
});
