// Task manager state
let currentTaskId = null;

// Utility functions
function setModalLoading(modalId, loading) {
    const loadingOverlay = document.getElementById(`${modalId}-loading`);
    if (loadingOverlay) {
        loadingOverlay.classList.toggle('d-none', !loading);
    }
}

// Get CSRF token from meta tag
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function setupEditor(editorId, modalId, options = {}) {
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

    const combinedOptions = Object.assign({}, defaultOptions, options);
    combinedOptions.selector = `#${editorId}`;
    
    return tinymce.init({
        ...combinedOptions,
        setup: function(editor) {
            setModalLoading(modalId, true);
            editor.on('init', function() {
                setModalLoading(modalId, false);
                $(`#${modalId}`).on('shown.bs.modal', function() {
                    editor.focus();
                });
            });
        }
    });
}

function resetTaskForm() {
    const form = document.getElementById('new-task-form');
    if (form) form.reset();
    
    const editor = tinymce.get('task-description');
    if (editor) {
        editor.setContent('');
        editor.getBody().contentEditable = true;
    }
    
    currentTaskId = null;
}

function getFormData() {
    const form = document.getElementById('new-task-form');
    const formData = {};
    
    new FormData(form).forEach((value, key) => {
        formData[key] = value;
    });

    const editor = tinymce.get('task-description');
    if (editor) {
        formData.description = editor.getContent();
    }

    return formData;
}

function setFormData(data, disabled = false) {
    const form = document.getElementById('new-task-form');
    
    Object.entries(data).forEach(([key, value]) => {
        const field = form.elements[key];
        if (field) {
            field.value = value || '';
            field.disabled = disabled;
        }
    });

    const editor = tinymce.get('task-description');
    if (editor) {
        editor.setContent(data.description || '');
        editor.getBody().contentEditable = !disabled;
    }
}

// Task CRUD operations
function addTask() {
    resetTaskForm();
    $('#modal-new-task').modal('show');
}

async function createTask() {
    try {
        setModalLoading('modal-new-task', true);
        const formData = getFormData();
        formData.project_id = window.projectId;

        const response = await fetch(`/projects/${window.projectId}/task`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to create task');
        }

        toastr.success('Task created successfully');
        location.reload();
    } catch (error) {
        toastr.error('Error creating task: ' + error.message);
        setModalLoading('modal-new-task', false);
    }
}

async function viewTask(taskId) {
    try {
        setModalLoading('modal-new-task', true);
        const response = await fetch(`/projects/task/${taskId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch task');
        }

        const result = await response.json();
        setFormData(result.task, true);
        
        $('#modal-new-task').modal('show');
        setModalLoading('modal-new-task', false);
    } catch (error) {
        toastr.error('Error viewing task: ' + error.message);
        setModalLoading('modal-new-task', false);
    }
}

async function editTask(taskId) {
    try {
        setModalLoading('modal-new-task', true);
        const response = await fetch(`/projects/task/${taskId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch task');
        }

        const result = await response.json();
        currentTaskId = taskId;
        setFormData(result.task, false);
        
        $('#modal-new-task').modal('show');
        setModalLoading('modal-new-task', false);
    } catch (error) {
        toastr.error('Error editing task: ' + error.message);
        setModalLoading('modal-new-task', false);
    }
}

async function updateTask() {
    if (!currentTaskId) {
        toastr.error('No task selected for update');
        return;
    }

    try {
        setModalLoading('modal-new-task', true);
        const formData = getFormData();

        const response = await fetch(`/projects/task/${currentTaskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to update task');
        }

        toastr.success('Task updated successfully');
        location.reload();
    } catch (error) {
        toastr.error('Error updating task: ' + error.message);
        setModalLoading('modal-new-task', false);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    try {
        setModalLoading('modal-new-task', true);
        const response = await fetch(`/projects/task/${taskId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': getCsrfToken()
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete task');
        }

        toastr.success('Task deleted successfully');
        location.reload();
    } catch (error) {
        toastr.error('Error deleting task: ' + error.message);
        setModalLoading('modal-new-task', false);
    }
}

function saveNewTask() {
    if (currentTaskId) {
        updateTask();
    } else {
        createTask();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize TinyMCE
    setupEditor('task-description', 'modal-new-task', {
        placeholder: 'Enter task description...'
    });

    // Reset form when modal is closed
    $('#modal-new-task').on('hidden.bs.modal', function() {
        resetTaskForm();
    });
});

// Make functions globally available
window.addTask = addTask;
window.viewTask = viewTask;
window.editTask = editTask;
window.deleteTask = deleteTask;
window.saveNewTask = saveNewTask;
