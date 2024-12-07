import { notifications, modal, api, forms } from './shared/utils.js';

class TaskManager {
    constructor() {
        this.currentTaskId = null;
        this.projectId = window.projectId; // Assuming projectId is set in the template
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Initialize TinyMCE
        modal.setupEditor('task-description', 'modal-new-task', {
            placeholder: 'Enter task description...'
        });

        // Reset form when modal is closed
        $('#modal-new-task').on('hidden.bs.modal', () => {
            this.resetTaskForm();
        });
    }

    resetTaskForm() {
        modal.resetForm('new-task-form', 'task-description');
        this.currentTaskId = null;
    }

    // Task CRUD operations
    async createTask() {
        try {
            modal.setLoading('modal-new-task', true);
            const formData = forms.getFormData('new-task-form', 'task-description');
            formData.project_id = this.projectId;

            const result = await api.fetchWithError(`/projects/${this.projectId}/task`, {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            notifications.showSuccess('Task created successfully');
            location.reload();
        } catch (error) {
            modal.setLoading('modal-new-task', false);
        }
    }

    async viewTask(taskId) {
        try {
            modal.setLoading('modal-new-task', true);
            const result = await api.fetchWithError(`/projects/task/${taskId}`);
            
            forms.setFormData('new-task-form', result.task, 'task-description', true);
            
            $('#modal-new-task').modal('show');
            modal.setLoading('modal-new-task', false);
        } catch (error) {
            modal.setLoading('modal-new-task', false);
        }
    }

    async editTask(taskId) {
        try {
            modal.setLoading('modal-new-task', true);
            const result = await api.fetchWithError(`/projects/task/${taskId}`);
            
            this.currentTaskId = taskId;
            forms.setFormData('new-task-form', result.task, 'task-description', false);
            
            $('#modal-new-task').modal('show');
            modal.setLoading('modal-new-task', false);
        } catch (error) {
            modal.setLoading('modal-new-task', false);
        }
    }

    async updateTask() {
        if (!this.currentTaskId) {
            notifications.showError('No task selected for update');
            return;
        }

        try {
            modal.setLoading('modal-new-task', true);
            const formData = forms.getFormData('new-task-form', 'task-description');

            await api.fetchWithError(`/projects/task/${this.currentTaskId}`, {
                method: 'PUT',
                body: JSON.stringify(formData)
            });

            notifications.showSuccess('Task updated successfully');
            location.reload();
        } catch (error) {
            modal.setLoading('modal-new-task', false);
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }

        try {
            modal.setLoading('modal-new-task', true);
            await api.fetchWithError(`/projects/task/${taskId}`, {
                method: 'DELETE'
            });

            notifications.showSuccess('Task deleted successfully');
            location.reload();
        } catch (error) {
            modal.setLoading('modal-new-task', false);
        }
    }

    // Task action handlers
    saveNewTask() {
        if (this.currentTaskId) {
            this.updateTask();
        } else {
            this.createTask();
        }
    }
}

// Initialize task manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.taskManager = new TaskManager();
});

// Export functions for use in HTML
window.viewTask = (taskId) => window.taskManager.viewTask(taskId);
window.editTask = (taskId) => window.taskManager.editTask(taskId);
window.deleteTask = (taskId) => window.taskManager.deleteTask(taskId);
window.saveNewTask = () => window.taskManager.saveNewTask();
