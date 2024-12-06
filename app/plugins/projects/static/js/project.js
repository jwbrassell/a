// Project view page functionality

// Todo functions
function createTodo() {
    const description = document.getElementById('todo-description').value;
    const assignedTo = document.getElementById('todo-assigned-to').value;
    
    fetch(`/projects/${projectId}/todo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            description: description,
            assigned_to_id: assignedTo || null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error creating todo: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating todo');
    });
}

function toggleTodo(todoId) {
    fetch(`/projects/todo/${todoId}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error updating todo: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating todo');
    });
}

function deleteTodo(todoId) {
    if (!confirm('Are you sure you want to delete this todo?')) {
        return;
    }

    fetch(`/projects/todo/${todoId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error deleting todo: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error deleting todo');
    });
}

// Task functions
function createTask() {
    const taskData = {
        name: document.getElementById('task-name').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        assigned_to_id: document.getElementById('task-assigned-to').value || null,
        due_date: document.getElementById('task-due-date').value || null
    };

    fetch(`/projects/${projectId}/task`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error creating task: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating task');
    });
}

function viewTask(taskId) {
    fetch(`/projects/task/${taskId}`)
    .then(response => response.json())
    .then(task => {
        const modal = document.getElementById('view-task-modal');
        const title = document.getElementById('view-task-title');
        const content = document.getElementById('view-task-content');

        title.textContent = task.name;
        content.innerHTML = `
            <div class="task-details">
                <div class="mb-3">
                    <h6>Description</h6>
                    <p>${task.description || 'No description provided'}</p>
                </div>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h6>Status</h6>
                        <span class="badge badge-${getStatusClass(task.status)}">${task.status}</span>
                    </div>
                    <div class="col-md-6">
                        <h6>Priority</h6>
                        <span class="badge badge-${getPriorityClass(task.priority)}">${task.priority}</span>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h6>Assigned To</h6>
                        <p>${task.assigned_to || 'Unassigned'}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Due Date</h6>
                        <p>${task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}</p>
                    </div>
                </div>
            </div>
        `;

        $(modal).modal('show');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error loading task details');
    });
}

function editTask(taskId) {
    // First load the task data
    fetch(`/projects/task/${taskId}`)
    .then(response => response.json())
    .then(task => {
        // Populate the create task modal with existing data
        document.getElementById('task-name').value = task.name;
        document.getElementById('task-description').value = task.description;
        document.getElementById('task-status').value = task.status;
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-assigned-to').value = task.assigned_to_id || '';
        document.getElementById('task-due-date').value = task.due_date ? task.due_date.split('T')[0] : '';

        // Change the modal button to update instead of create
        const modalFooter = document.querySelector('#create-task-modal .modal-footer');
        modalFooter.innerHTML = `
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" onclick="updateTask(${taskId})">Update Task</button>
        `;

        // Show the modal
        $('#create-task-modal').modal('show');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error loading task details');
    });
}

function updateTask(taskId) {
    const taskData = {
        name: document.getElementById('task-name').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        assigned_to_id: document.getElementById('task-assigned-to').value || null,
        due_date: document.getElementById('task-due-date').value || null
    };

    fetch(`/projects/task/${taskId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error updating task: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating task');
    });
}

function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    fetch(`/projects/task/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error deleting task: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error deleting task');
    });
}

// Comment functions
function submitComment(event) {
    event.preventDefault();
    
    const content = document.getElementById('comment-content').value;
    
    fetch(`/projects/${projectId}/comment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error posting comment: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error posting comment');
    });
}

function deleteComment(commentId) {
    if (!confirm('Are you sure you want to delete this comment?')) {
        return;
    }

    fetch(`/projects/comment/${commentId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error deleting comment: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error deleting comment');
    });
}

// Utility functions
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
