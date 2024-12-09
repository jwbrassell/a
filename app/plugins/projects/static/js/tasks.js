/**
 * @typedef {Object} TaskManager
 */

/** @type {TaskManager} */
const TaskManager = {
    init() {
        console.log('Initializing TaskManager');
        this.bindEvents();
        this.initTodoHandlers();
        this.initRichTextEditor();
        this.initStatusPriorityHandlers();
        this.initCommentHandlers();
        this.tempTaskId = null;
        this.currentTaskId = window.APP?.taskId || null;
        this.autoSaveTimeout = null;
        this.deletedTodoIds = new Set(); // Track deleted todo IDs
    },

    generateTempId() {
        return 'temp_' + Math.random().toString(36).substr(2, 9);
    },

    bindEvents() {
        console.log('Binding events');
        const taskForm = document.getElementById('taskForm');
        if (taskForm) {
            taskForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

        const addTaskBtn = document.getElementById('addTaskBtn');
        if (addTaskBtn) {
            addTaskBtn.addEventListener('click', () => {
                this.tempTaskId = this.generateTempId();
                this.currentTaskId = null;
                this.resetTaskForm();
                $('#taskModal').modal('show');
            });
        }
    },

    initCommentHandlers() {
        const addCommentBtn = document.getElementById('addTaskCommentBtn');
        if (addCommentBtn) {
            addCommentBtn.addEventListener('click', () => this.addComment());
        }
    },

    async addComment() {
        if (!this.currentTaskId) return;

        const commentInput = document.getElementById('taskCommentInput');
        const content = commentInput.value.trim();
        if (!content) return;

        try {
            const response = await fetch(`/projects/task/${this.currentTaskId}/comment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({ content })
            });

            const result = await response.json();
            if (result.success) {
                // Clear input
                commentInput.value = '';
                
                // Add comment to list
                const commentsList = document.getElementById('taskCommentsList');
                const comment = result.comment;
                const commentHtml = `
                    <div class="direct-chat-msg">
                        <div class="direct-chat-infos clearfix">
                            <span class="direct-chat-name float-left">${comment.user}</span>
                            <span class="direct-chat-timestamp float-right">${comment.created_at}</span>
                        </div>
                        <img class="direct-chat-img" src="${comment.user_avatar}" alt="User Image">
                        <div class="direct-chat-text">${comment.content}</div>
                    </div>
                `;
                commentsList.insertAdjacentHTML('beforeend', commentHtml);
                
                // Scroll to bottom
                commentsList.scrollTop = commentsList.scrollHeight;
                
                toastr.success('Comment added successfully');
            } else {
                toastr.error(result.message || 'Error adding comment');
            }
        } catch (error) {
            console.error('Error adding comment:', error);
            toastr.error('Error adding comment');
        }
    },

    initTodoHandlers() {
        console.log('Initializing todo handlers');
        // Handle todo buttons in both modal and edit page
        const addTodoBtn = document.querySelector('#addTaskTodoBtn');
        if (addTodoBtn) {
            console.log('Found addTodoBtn, binding click handler');
            addTodoBtn.addEventListener('click', () => this.addTodoItem());
        }

        const todoList = document.querySelector('#taskTodoList');
        if (todoList) {
            console.log('Found todoList, binding event handlers');
            // Handle todo removal
            todoList.addEventListener('click', (e) => {
                if (e.target.classList.contains('remove-todo') || e.target.closest('.remove-todo')) {
                    const todoRow = e.target.closest('tr');
                    const todoId = todoRow.dataset.todoId;
                    console.log('Removing todo:', todoId);
                    
                    if (!todoId.startsWith('new_')) {
                        this.deletedTodoIds.add(todoId);
                    }
                    
                    todoRow.remove();
                    this.reindexTodos();
                    this.autoSave();
                }
            });

            // Handle checkbox changes
            todoList.addEventListener('change', (e) => {
                if (e.target.classList.contains('todo-checkbox')) {
                    const row = e.target.closest('tr');
                    const description = row.querySelector('.todo-description');
                    if (description) {
                        if (e.target.checked) {
                            description.classList.add('text-muted', 'text-decoration-line-through');
                        } else {
                            description.classList.remove('text-muted', 'text-decoration-line-through');
                        }
                        this.autoSave();
                    }
                }
            });

            // Handle todo description and due date changes
            todoList.addEventListener('change', (e) => {
                if (e.target.classList.contains('todo-description') || 
                    e.target.classList.contains('todo-due-date')) {
                    this.autoSave();
                }
            });
        }
    },

    initStatusPriorityHandlers() {
        const statusSelects = document.querySelectorAll('select[name="status"]');
        const prioritySelects = document.querySelectorAll('select[name="priority"]');

        statusSelects.forEach(select => {
            this.updateSelectColor(select);
            select.addEventListener('change', () => this.updateSelectColor(select));
        });

        prioritySelects.forEach(select => {
            this.updateSelectColor(select);
            select.addEventListener('change', () => this.updateSelectColor(select));
        });
    },

    updateSelectColor(select) {
        if (!select) return;
        const selectedOption = select.options[select.selectedIndex];
        if (!selectedOption) return;
        const color = selectedOption.dataset.color;
        select.className = color ? 
            `form-select bg-${color} text-light border-secondary` : 
            'form-select bg-dark text-light border-secondary';
    },

    initRichTextEditor() {
        const descriptionField = document.querySelector('textarea[name="description"]');
        if (descriptionField && typeof tinymce !== 'undefined') {
            // Remove any existing editor instance
            tinymce.remove('textarea[name="description"]');
            
            // Initialize new editor
            tinymce.init({
                selector: 'textarea[name="description"]',
                height: 300,
                menubar: false,
                skin: 'oxide-dark',
                content_css: 'dark',
                plugins: [
                    'advlist autolink lists link image charmap print preview anchor',
                    'searchreplace visualblocks code fullscreen',
                    'insertdatetime media table paste code help wordcount'
                ],
                toolbar: 'undo redo | formatselect | bold italic backcolor | ' +
                        'alignleft aligncenter alignright alignjustify | ' +
                        'bullist numlist outdent indent | removeformat | help',
                setup(editor) {
                    editor.on('change', function() {
                        editor.save();
                    });
                }
            });
        }
    },

    autoSave() {
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }
        
        this.autoSaveTimeout = setTimeout(() => {
            if (this.currentTaskId) {
                console.log('Auto-saving task');
                const url = `/projects/task/${this.currentTaskId}`;
                const data = this.collectFormData();
                this.saveData(url, 'PUT', data);
            }
        }, 1000);
    },

    collectFormData() {
        const form = document.getElementById('taskForm');
        if (!form) return null;

        const data = {};

        // Process all form fields except todos
        for (let i = 0; i < form.elements.length; i++) {
            const element = form.elements[i];
            
            if (!element.name || element.name.startsWith('todos[')) continue;
            if (element.type === 'submit' || element.tagName === 'FIELDSET') continue;

            if (element.type === 'checkbox') {
                data[element.name] = element.checked;
            } else if (element.type === 'select-multiple') {
                data[element.name] = Array.from(element.selectedOptions).map(option => option.value);
            } else {
                const value = element.value.trim();
                if (value !== '') {
                    data[element.name] = value;
                }
            }
        }

        // Add project ID
        if (window.APP && window.APP.projectId) {
            data.project_id = window.APP.projectId;
        }

        // Process todos
        const todos = [];
        const todoRows = document.querySelectorAll('#taskTodoList tr[data-todo-id]');
        
        todoRows.forEach((row, index) => {
            const description = row.querySelector('.todo-description');
            const todoId = row.dataset.todoId;
            
            if (!description || 
                !description.value.trim() || 
                this.deletedTodoIds.has(todoId)) {
                return;
            }

            const todo = {
                description: description.value.trim(),
                completed: row.querySelector('.todo-checkbox')?.checked || false,
                due_date: row.querySelector('.todo-due-date')?.value || null,
                id: todoId.startsWith('new_') ? null : todoId
            };
            todos.push(todo);
        });

        if (todos.length > 0) {
            data.todos = todos;
        }

        // Add deleted todos
        if (this.deletedTodoIds.size > 0) {
            data.deleted_todos = Array.from(this.deletedTodoIds);
        }

        console.log('Collected form data:', data);
        return data;
    },

    saveData(url, method, data) {
        console.log(`Sending ${method} request to ${url}`);
        return fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            console.log('Server response:', result);
            if (result.success) {
                toastr.success('Changes saved successfully');
                if (method === 'POST' || (method === 'PUT' && !this.autoSaveTimeout)) {
                    if (document.getElementById('taskModal')) {
                        $('#taskModal').modal('hide');
                    }
                    location.reload();
                }
            } else {
                toastr.error(result.message || 'Error saving changes');
            }
            return result;
        })
        .catch(error => {
            console.error('Error:', error);
            toastr.error('Error saving changes');
            throw error;
        });
    },

    handleFormSubmit(e) {
        e.preventDefault();
        console.log('Form submitted');
        
        if (typeof tinymce !== 'undefined') {
            const editor = tinymce.get('task-description');
            if (editor) {
                editor.save();
            }
        }

        const data = this.collectFormData();
        if (!data) return;

        console.log('Final form data:', data);

        // Determine if we're creating or updating a task
        let url, method;
        if (this.currentTaskId) {
            // Updating existing task
            url = `/projects/task/${this.currentTaskId}`;
            method = 'PUT';
        } else {
            // Creating new task
            url = `/projects/${window.APP.projectId}/task`;
            method = 'POST';
        }
        console.log(`Using ${method} ${url}`);

        this.saveData(url, method, data)
            .then(result => {
                if (result.success) {
                    if (document.getElementById('taskModal')) {
                        $('#taskModal').modal('hide');
                    }
                    location.reload();
                }
            })
            .catch(error => {
                console.error('Error in form submission:', error);
            });
    },

    editTask(taskId) {
        console.log('Editing task:', taskId);
        this.currentTaskId = taskId;
        this.deletedTodoIds.clear(); // Reset deleted todos tracking
        
        fetch(`/projects/task/${taskId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Received task data:', data);
                if (data.success) {
                    const task = data.task;
                    const taskModal = document.getElementById('taskModal');
                    if (!taskModal) return;
                    
                    taskModal.querySelector('#task-name').value = task.name;
                    taskModal.querySelector('#task-summary').value = task.summary || '';
                    
                    if (typeof tinymce !== 'undefined') {
                        const editor = tinymce.get('task-description');
                        if (editor) {
                            editor.setContent(task.description || '');
                        }
                    } else {
                        taskModal.querySelector('#task-description').value = task.description || '';
                    }
                    
                    const statusSelect = taskModal.querySelector('#task-status');
                    const prioritySelect = taskModal.querySelector('#task-priority');
                    if (statusSelect) statusSelect.value = task.status || '';
                    if (prioritySelect) prioritySelect.value = task.priority || '';
                    
                    this.updateSelectColor(statusSelect);
                    this.updateSelectColor(prioritySelect);
                    
                    const assignedSelect = taskModal.querySelector('#task-assigned');
                    if (assignedSelect) assignedSelect.value = task.assigned_to_id || '';
                    
                    const dueDateInput = taskModal.querySelector('#task-due-date');
                    if (dueDateInput) dueDateInput.value = task.due_date || '';
                    
                    // Load todos
                    const todoList = taskModal.querySelector('#taskTodoList');
                    if (todoList && task.todos && task.todos.length > 0) {
                        todoList.innerHTML = task.todos.map((todo, index) => `
                            <tr data-todo-id="${todo.id || `existing_${index}`}">
                                <td class="text-center">
                                    <div class="form-check">
                                        <input type="checkbox" class="form-check-input todo-checkbox" 
                                               id="todoCheck_${index}" 
                                               name="todos[${index}][completed]"
                                               ${todo.completed ? 'checked' : ''}>
                                        <label class="form-check-label" for="todoCheck_${index}"></label>
                                    </div>
                                </td>
                                <td>
                                    <input type="text" class="form-control form-control-sm todo-description" 
                                           name="todos[${index}][description]"
                                           value="${todo.description}"
                                           required>
                                </td>
                                <td>
                                    <input type="date" class="form-control form-control-sm todo-due-date"
                                           name="todos[${index}][due_date]"
                                           value="${todo.due_date || ''}">
                                </td>
                                <td class="text-center">
                                    <button type="button" class="btn btn-danger btn-sm remove-todo" title="Remove Todo">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('');
                    } else if (todoList) {
                        todoList.innerHTML = `
                            <tr>
                                <td colspan="4" class="text-center text-muted">
                                    No todo items found.
                                </td>
                            </tr>
                        `;
                    }

                    // Load comments
                    const commentsList = taskModal.querySelector('#taskCommentsList');
                    if (commentsList && task.comments && task.comments.length > 0) {
                        commentsList.innerHTML = task.comments.map(comment => `
                            <div class="direct-chat-msg">
                                <div class="direct-chat-infos clearfix">
                                    <span class="direct-chat-name float-left">${comment.user}</span>
                                    <span class="direct-chat-timestamp float-right">${comment.created_at}</span>
                                </div>
                                <img class="direct-chat-img" src="${comment.user_avatar}" alt="User Image">
                                <div class="direct-chat-text">${comment.content}</div>
                            </div>
                        `).join('');
                    } else if (commentsList) {
                        commentsList.innerHTML = '<div class="text-center text-muted">No comments yet</div>';
                    }
                    
                    $('#taskModal').modal('show');
                } else {
                    toastr.error(data.message || 'Error loading task');
                }
            })
            .catch(error => {
                console.error('Error loading task:', error);
                toastr.error('Error loading task');
            });
    },

    resetTaskForm() {
        const form = document.getElementById('taskForm');
        if (!form) return;

        form.reset();
        this.deletedTodoIds.clear(); // Reset deleted todos tracking
        
        if (typeof tinymce !== 'undefined') {
            const editor = tinymce.get('task-description');
            if (editor) {
                editor.setContent('');
            }
        }
        
        const selects = form.querySelectorAll('select[name="status"], select[name="priority"]');
        selects.forEach(select => this.updateSelectColor(select));
        
        const todoList = document.querySelector('#taskTodoList');
        if (todoList) {
            todoList.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted">
                        No todo items found.
                    </td>
                </tr>
            `;
        }

        const commentsList = document.querySelector('#taskCommentsList');
        if (commentsList) {
            commentsList.innerHTML = '<div class="text-center text-muted">No comments yet</div>';
        }
    },

    addTodoItem() {
        console.log('Adding new todo item');
        const todoList = document.querySelector('#taskTodoList');
        if (!todoList) return;

        const noTodosRow = todoList.querySelector('tr td[colspan]');
        if (noTodosRow) {
            noTodosRow.remove();
        }

        const index = todoList.getElementsByTagName('tr').length;
        console.log('New todo index:', index);
        const template = `
            <tr data-todo-id="new_${index}">
                <td class="text-center">
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input todo-checkbox" 
                               id="todoCheck_new_${index}" 
                               name="todos[${index}][completed]">
                        <label class="form-check-label" for="todoCheck_new_${index}"></label>
                    </div>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm todo-description" 
                           name="todos[${index}][description]"
                           required>
                </td>
                <td>
                    <input type="date" class="form-control form-control-sm todo-due-date"
                           name="todos[${index}][due_date]">
                </td>
                <td class="text-center">
                    <button type="button" class="btn btn-danger btn-sm remove-todo" title="Remove Todo">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        todoList.insertAdjacentHTML('beforeend', template);

        const newRow = todoList.lastElementChild;
        const descriptionInput = newRow.querySelector('.todo-description');
        if (descriptionInput) {
            descriptionInput.focus();
        }
    },

    reindexTodos() {
        const todoList = document.querySelector('#taskTodoList');
        if (!todoList) return;

        const todos = todoList.getElementsByTagName('tr');
        
        if (todos.length === 0) {
            todoList.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted">
                        No todo items found.
                    </td>
                </tr>
            `;
            return;
        }

        Array.from(todos).forEach((todo, index) => {
            const checkbox = todo.querySelector('.todo-checkbox');
            const description = todo.querySelector('.todo-description');
            const dueDate = todo.querySelector('.todo-due-date');

            if (checkbox) checkbox.name = `todos[${index}][completed]`;
            if (description) description.name = `todos[${index}][description]`;
            if (dueDate) dueDate.name = `todos[${index}][due_date]`;
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing TaskManager');
    TaskManager.init();
    window.editTask = function(taskId) {
        TaskManager.editTask(taskId);
    };
});
