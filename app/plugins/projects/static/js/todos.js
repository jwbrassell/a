// Todo module using IIFE to prevent global scope pollution
window.todoModule = (function() {
    function resetTodoForm() {
        document.getElementById('new-todo-form').reset();
        window.currentTodoId = null;
    }

    // Todo CRUD operations
    async function createTodo() {
        try {
            const formData = {
                description: document.getElementById('todo-description').value,
                due_date: document.getElementById('todo-due-date').value,
                project_id: window.projectId
            };

            const response = await fetch('/projects/todos/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': projectModule.getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Failed to create todo');
            }

            projectModule.showSuccess('Todo created successfully');
            location.reload(); // Refresh to show new todo
        } catch (error) {
            projectModule.showError('Error creating todo: ' + error.message);
        }
    }

    async function toggleTodo(todoId, completed) {
        try {
            const response = await fetch(`/projects/todos/${todoId}/toggle`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': projectModule.getCsrfToken()
                },
                body: JSON.stringify({ completed })
            });

            if (!response.ok) {
                throw new Error('Failed to update todo status');
            }

            // Update the todo item appearance
            const todoRow = document.querySelector(`tr[data-todo-id="${todoId}"]`);
            if (todoRow) {
                const descriptionSpan = todoRow.querySelector('td:nth-child(3) span');
                if (completed) {
                    descriptionSpan.classList.add('text-muted', 'text-decoration-line-through');
                } else {
                    descriptionSpan.classList.remove('text-muted', 'text-decoration-line-through');
                }
            }

            projectModule.showSuccess('Todo status updated');
        } catch (error) {
            // Revert checkbox state on error
            const checkbox = document.getElementById(`todoCheck${todoId}`);
            if (checkbox) {
                checkbox.checked = !completed;
            }
            projectModule.showError('Error updating todo: ' + error.message);
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
            const modal = new bootstrap.Modal(document.getElementById('modal-new-todo'));
            modal.show();
        } catch (error) {
            projectModule.showError('Error editing todo: ' + error.message);
        }
    }

    async function updateTodo() {
        if (!window.currentTodoId) {
            projectModule.showError('No todo selected for update');
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
                    'X-CSRF-TOKEN': projectModule.getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('Failed to update todo');
            }

            projectModule.showSuccess('Todo updated successfully');
            location.reload(); // Refresh to show updated todo
        } catch (error) {
            projectModule.showError('Error updating todo: ' + error.message);
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
                    'X-CSRF-TOKEN': projectModule.getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete todo');
            }

            // Remove the todo item from the DOM
            const todoRow = document.querySelector(`tr[data-todo-id="${todoId}"]`);
            if (todoRow) {
                todoRow.remove();
            }

            projectModule.showSuccess('Todo deleted successfully');
        } catch (error) {
            projectModule.showError('Error deleting todo: ' + error.message);
        }
    }

    async function updateTodoOrder() {
        try {
            // Get all todo rows
            const todoRows = Array.from(document.querySelectorAll('tr[data-todo-id]'));
            const todos = todoRows.map((row, index) => ({
                id: parseInt(row.getAttribute('data-todo-id')),
                sort_order: index  // Changed from 'order' to 'sort_order'
            }));

            const response = await fetch('/projects/todo/reorder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': projectModule.getCsrfToken()
                },
                body: JSON.stringify({ todos })
            });

            if (!response.ok) {
                throw new Error('Failed to update todo order');
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Failed to update todo order');
            }

        } catch (error) {
            projectModule.showError('Error updating todo order: ' + error.message);
            location.reload(); // Refresh to restore correct order
        }
    }

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize Sortable
        const todoList = document.querySelector('.sortable-todos');
        if (todoList) {
            new Sortable(todoList, {
                handle: '.handle',
                animation: 150,
                onStart: function() {
                    // Prevent the browser from showing unsaved changes warning
                    window.onbeforeunload = null;
                },
                onEnd: function() {
                    updateTodoOrder();
                }
            });
        }

        // Handle collapse icon changes
        const todoCollapse = document.getElementById('todoCollapse');
        const collapseIcon = document.querySelector('.collapse-icon');
        
        if (todoCollapse && collapseIcon) {
            todoCollapse.addEventListener('show.bs.collapse', function() {
                collapseIcon.classList.remove('fa-plus');
                collapseIcon.classList.add('fa-minus');
            });
            
            todoCollapse.addEventListener('hide.bs.collapse', function() {
                collapseIcon.classList.remove('fa-minus');
                collapseIcon.classList.add('fa-plus');
            });
        }

        // Reset form when modal is closed
        const todoModal = document.getElementById('modal-new-todo');
        if (todoModal) {
            todoModal.addEventListener('hidden.bs.modal', function () {
                resetTodoForm();
            });
        }

        // Clear any existing beforeunload handler when the page loads
        window.onbeforeunload = null;
    });

    // Public API
    return {
        createTodo,
        toggleTodo,
        editTodo,
        updateTodo,
        deleteTodo
    };
})();
