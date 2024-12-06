// Project functionality
function toggleTodo(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    const checkbox = document.getElementById(`todo-${id}`);
    fetch(`/projects/todo/${id}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
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
        }
    });
}

function createTodo() {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    const description = document.getElementById('todo-description').value;
    const assignedTo = document.getElementById('todo-assigned-to').value;
    const projectId = window.location.pathname.split('/').pop();

    fetch('/projects/todo/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            project_id: projectId,
            description: description,
            assigned_to_id: assignedTo || null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    });
}

function deleteTodo(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    if (confirm('Are you sure you want to delete this todo?')) {
        fetch(`/projects/todo/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
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
        },
        body: JSON.stringify({ todos: todos })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to update todo order');
        }
    });
}

function createTask() {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    const form = document.getElementById('task-form');
    const projectId = window.location.pathname.split('/').pop();
    const formData = {
        project_id: projectId,
        name: document.getElementById('task-name').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        assigned_to_id: document.getElementById('task-assigned-to').value || null,
        due_date: document.getElementById('task-due-date').value || null
    };

    fetch('/projects/task/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    });
}

function editTask(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    fetch(`/projects/task/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const task = data.task;
                // Populate modal with task data
                document.getElementById('task-name').value = task.name;
                document.getElementById('task-description').value = task.description;
                document.getElementById('task-status').value = task.status;
                document.getElementById('task-priority').value = task.priority;
                document.getElementById('task-assigned-to').value = task.assigned_to_id || '';
                document.getElementById('task-due-date').value = task.due_date || '';
                
                // Show modal
                $('#create-task-modal').modal('show');
            }
        });
}

function deleteTask(id) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    if (confirm('Are you sure you want to delete this task?')) {
        fetch(`/projects/task/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
}

function submitComment(event) {
    // If can_edit is false, return without doing anything
    if (!window.canEdit) return;

    event.preventDefault();
    const content = document.getElementById('comment-content').value;
    const projectId = window.location.pathname.split('/').pop();

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
        if (data.success) {
            location.reload();
            // Clear the comment input
            document.getElementById('comment-content').value = '';
        }
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
            iconGrid.appendChild(div);
        });
    });

    // Add floating save/cancel buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'position-fixed bottom-0 end-0 p-3';
    buttonContainer.style.zIndex = '1050';
    buttonContainer.innerHTML = `
        <div class="btn-group">
            <button type="button" class="btn btn-secondary" onclick="$('#icon-picker-modal').modal('hide')">Cancel</button>
            <button type="button" class="btn btn-primary" onclick="saveSelectedIcon()">Save</button>
        </div>
    `;
    document.getElementById('icon-picker-modal').appendChild(buttonContainer);
}

// Initialize icon picker when modal is shown
$('#icon-picker-modal').on('show.bs.modal', function () {
    if (!document.querySelector('#icon-grid .icon-option')) {
        loadIcons();
    }
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
        $('#icon-picker-modal').modal('hide');
    }
}

// Add click handler for icon selection
document.getElementById('icon-grid')?.addEventListener('click', function(e) {
    const iconOption = e.target.closest('.icon-option');
    if (iconOption) {
        // Remove selection from other icons
        document.querySelectorAll('.icon-option.selected').forEach(el => {
            el.classList.remove('selected');
        });
        // Add selection to clicked icon
        iconOption.classList.add('selected');
    }
});
