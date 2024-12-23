// Todo module using IIFE to prevent global scope pollution
window.todoModule = (function() {
    // Get CSRF token from meta tag
    function getCsrfToken() {
        console.log('Getting CSRF token'); // Debug log
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!token) {
            console.error('CSRF token not found in meta tag');
            return '';
        }
        console.log('CSRF token found'); // Debug log
        return token;
    }

    // Show error message
    function showError(message) {
        if (window.projectModule) {
            window.projectModule.showError(message);
        } else {
            console.error(message);
        }
    }

    // Show success message
    function showSuccess(message) {
        if (window.projectModule) {
            window.projectModule.showSuccess(message);
        } else {
            console.log(message);
        }
    }

    // Todo CRUD operations
    async function createTodo() {
        console.log('createTodo called'); // Debug log
        try {
            const description = document.getElementById('todo-description').value;
            if (!description) {
                throw new Error('Description is required');
            }

            const formData = {
                description: description,
                due_date: document.getElementById('todo-due-date').value
            };

            console.log('Sending request with data:', formData); // Debug log
            const token = getCsrfToken();
            console.log('Using CSRF token:', token); // Debug log

            const response = await fetch(`/projects/${window.projectId}/todos`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': token
                },
                body: JSON.stringify(formData)
            });

            console.log('Response status:', response.status); // Debug log

            if (!response.ok) {
                const text = await response.text();
                console.log('Error response:', text); // Debug log
                throw new Error('Failed to create todo');
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Failed to create todo');
            }

            showSuccess('Todo created successfully');
            location.reload(); // Refresh to show new todo
        } catch (error) {
            console.error('Error in createTodo:', error); // Debug log
            showError('Error creating todo: ' + error.message);
        }
    }

    async function toggleTodo(todoId, completed) {
        console.log('toggleTodo called with id:', todoId, 'completed:', completed); // Debug log
        try {
            const response = await fetch(`/projects/todo/${todoId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': getCsrfToken()
                },
                body: JSON.stringify({ completed })
            });

            if (!response.ok) {
                throw new Error('Failed to update todo status');
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Failed to update todo status');
            }

            // Update the todo item appearance
            const todoRow = document.querySelector(`tr[data-todo-id="${todoId}"]`);
            if (todoRow) {
                const descriptionSpan = todoRow.querySelector('.todo-text');
                if (completed) {
                    descriptionSpan.classList.add('text-muted', 'text-decoration-line-through');
                } else {
                    descriptionSpan.classList.remove('text-muted', 'text-decoration-line-through');
                }
            }

            showSuccess('Todo status updated');
        } catch (error) {
            // Revert checkbox state on error
            const checkbox = document.getElementById(`todoCheck${todoId}`);
            if (checkbox) {
                checkbox.checked = !completed;
            }
            showError('Error updating todo: ' + error.message);
        }
    }

    async function editTodo(todoId) {
        console.log('editTodo called with id:', todoId); // Debug log
        try {
            const response = await fetch(`/projects/todo/${todoId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch todo details');
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Failed to fetch todo details');
            }

            const todo = result.todo;

            // Switch to edit mode
            const todoRow = document.querySelector(`tr[data-todo-id="${todoId}"]`);
            if (todoRow) {
                const descriptionCell = todoRow.querySelector('td:nth-child(2)');
                const dueDateCell = todoRow.querySelector('td:nth-child(3)');
                const actionsCell = todoRow.querySelector('td:nth-child(4)');

                // Save original content for cancel
                todoRow.dataset.originalDescription = todo.description;
                todoRow.dataset.originalDueDate = todo.due_date || '';

                // Replace with edit fields
                descriptionCell.innerHTML = `<input type="text" class="form-control form-control-sm" value="${todo.description}" required>`;
                dueDateCell.innerHTML = `<input type="date" class="form-control form-control-sm" value="${todo.due_date || ''}">`;
                actionsCell.innerHTML = `
                    <button type="button" class="btn btn-success btn-sm me-1" onclick="todoModule.updateTodo(${todoId})">
                        <i class="fas fa-check"></i>
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="todoModule.cancelEdit(${todoId})">
                        <i class="fas fa-times"></i>
                    </button>
                `;

                // Focus the description input
                descriptionCell.querySelector('input').focus();
            }
        } catch (error) {
            showError('Error editing todo: ' + error.message);
        }
    }

    async function updateTodo(todoId) {
        console.log('updateTodo called with id:', todoId); // Debug log
        try {
            const todoRow = document.querySelector(`tr[data-todo-id="${todoId}"]`);
            if (!todoRow) {
                throw new Error('Todo row not found');
            }

            const description = todoRow.querySelector('td:nth-child(2) input').value;
            const dueDate = todoRow.querySelector('td:nth-child(3) input').value;

            if (!description) {
                throw new Error('Description is required');
            }

            const formData = {
                description: description,
                due_date: dueDate
            };

            const response = await fetch(`/projects/todo/${todoId}`, {
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

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Failed to update todo');
            }

            showSuccess('Todo updated successfully');
            location.reload(); // Refresh to show updated todo
        } catch (error) {
            showError('Error updating todo: ' + error.message);
        }
    }

    function cancelEdit(todoId) {
        console.log('cancelEdit called with id:', todoId); // Debug log
        const todoRow = document.querySelector(`tr[data-todo-id="${todoId}"]`);
        if (todoRow) {
            const description = todoRow.dataset.originalDescription;
            const dueDate = todoRow.dataset.originalDueDate;

            const descriptionCell = todoRow.querySelector('td:nth-child(2)');
            const dueDateCell = todoRow.querySelector('td:nth-child(3)');
            const actionsCell = todoRow.querySelector('td:nth-child(4)');

            // Restore original content
            descriptionCell.innerHTML = `<span class="todo-text">${description}</span>`;
            dueDateCell.innerHTML = dueDate ? 
                `<span class="badge bg-info due-date-badge"><i class="far fa-clock me-1"></i>${dueDate}</span>` : '';
            actionsCell.innerHTML = `
                <button type="button" class="btn btn-primary btn-sm me-1" onclick="todoModule.editTodo(${todoId})">
                    <i class="fas fa-edit"></i>
                </button>
                <button type="button" class="btn btn-danger btn-sm" onclick="todoModule.deleteTodo(${todoId})">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        }
    }

    async function deleteTodo(todoId) {
        console.log('deleteTodo called with id:', todoId); // Debug log
        if (!confirm('Are you sure you want to delete this todo item?')) {
            return;
        }

        try {
            const response = await fetch(`/projects/todo/${todoId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRF-TOKEN': getCsrfToken()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete todo');
            }

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Failed to delete todo');
            }

            // Remove the todo item from the DOM
            const todoRow = document.querySelector(`tr[data-todo-id="${todoId}"]`);
            if (todoRow) {
                todoRow.remove();
            }

            showSuccess('Todo deleted successfully');
        } catch (error) {
            showError('Error deleting todo: ' + error.message);
        }
    }

    function showNewTodoForm() {
        console.log('showNewTodoForm called'); // Debug log
        const newTodoRow = document.getElementById('newTodoRow');
        console.log('newTodoRow:', newTodoRow); // Debug log
        if (newTodoRow) {
            console.log('Removing d-none class'); // Debug log
            newTodoRow.classList.remove('d-none');
            const todoDescription = document.getElementById('todo-description');
            if (todoDescription) {
                todoDescription.focus();
                console.log('Focused todo description input'); // Debug log
            }
            const addTodoBtn = document.getElementById('addTodoBtn');
            if (addTodoBtn) {
                addTodoBtn.disabled = true;
                console.log('Disabled add todo button'); // Debug log
            }
        }
    }

    function hideNewTodoForm() {
        console.log('hideNewTodoForm called'); // Debug log
        const newTodoRow = document.getElementById('newTodoRow');
        if (newTodoRow) {
            newTodoRow.classList.add('d-none');
            const todoDescription = document.getElementById('todo-description');
            if (todoDescription) {
                todoDescription.value = '';
            }
            const todoDueDate = document.getElementById('todo-due-date');
            if (todoDueDate) {
                todoDueDate.value = '';
            }
            const addTodoBtn = document.getElementById('addTodoBtn');
            if (addTodoBtn) {
                addTodoBtn.disabled = false;
            }
            console.log('Form hidden and fields reset'); // Debug log
        }
    }

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOMContentLoaded event fired in todos.js'); // Debug log

        // Todo checkbox change handlers
        const todoCheckboxes = document.querySelectorAll('.todo-checkbox');
        todoCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const todoId = this.closest('tr').dataset.todoId;
                toggleTodo(todoId, this.checked);
            });
        });

        // Handle Enter key in description field
        const todoDescription = document.getElementById('todo-description');
        if (todoDescription) {
            todoDescription.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    createTodo();
                }
            });
        }

        // Add click handler for Add Todo button
        const addTodoBtn = document.getElementById('addTodoBtn');
        if (addTodoBtn) {
            console.log('Found Add Todo button, adding click handler'); // Debug log
            addTodoBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Add Todo button clicked'); // Debug log
                showNewTodoForm();
            });
        } else {
            console.log('Add Todo button not found'); // Debug log
        }

        console.log('Todo event handlers initialized'); // Debug log
    });

    // Public API
    return {
        createTodo,
        toggleTodo,
        editTodo,
        updateTodo,
        cancelEdit,
        deleteTodo,
        showNewTodoForm,
        hideNewTodoForm
    };
})();

// Debug log when module is loaded
console.log('todoModule loaded with functions:', Object.keys(window.todoModule).join(', ')); // Debug log
