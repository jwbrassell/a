// Task Management Module
const TaskManager = {
    init: function() {
        this.bindEvents();
        this.initTodoHandlers();
        this.initRichTextEditor();
        this.initStatusPriorityHandlers();
        this.tempTaskId = null;
    },

    generateTempId: function() {
        return 'temp_' + Math.random().toString(36).substr(2, 9);
    },

    bindEvents: function() {
        // Handle task form submission
        const taskForm = document.getElementById('taskForm');
        if (taskForm) {
            taskForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

        // Handle "Add Task" button click
        const addTaskBtn = document.getElementById('addTaskBtn');
        if (addTaskBtn) {
            addTaskBtn.addEventListener('click', () => {
                this.tempTaskId = this.generateTempId();
                this.resetTaskForm();
                $('#taskModal').modal('show');
            });
        }

        // Handle comment form submission
        const commentInput = document.getElementById('commentInput');
        const commentBtn = document.querySelector('button[onclick="addComment()"]');
        if (commentBtn) {
            commentBtn.onclick = (e) => {
                e.preventDefault();
                this.addComment();
            };
        }
    },

    initStatusPriorityHandlers: function() {
        // Update status and priority select colors
        const statusSelects = document.querySelectorAll('select[name="status"], select[name*="[status]"]');
        const prioritySelects = document.querySelectorAll('select[name="priority"], select[name*="[priority]"]');

        statusSelects.forEach(select => {
            this.updateSelectColor(select);
            select.addEventListener('change', () => this.updateSelectColor(select));
        });

        prioritySelects.forEach(select => {
            this.updateSelectColor(select);
            select.addEventListener('change', () => this.updateSelectColor(select));
        });
    },

    updateSelectColor: function(select) {
        const selectedOption = select.options[select.selectedIndex];
        const color = selectedOption.dataset.color;
        if (color) {
            select.className = `form-select bg-${color} text-light border-secondary`;
        } else {
            select.className = 'form-select bg-dark text-light border-secondary';
        }
    },

    initTodoHandlers: function() {
        // Add todo button
        const addTodoBtn = document.getElementById('addTodoBtn');
        if (addTodoBtn) {
            addTodoBtn.addEventListener('click', this.addTodoItem.bind(this));
        }

        // Todo list event delegation
        const todoList = document.getElementById('todoList');
        if (todoList) {
            todoList.addEventListener('click', (e) => {
                if (e.target.classList.contains('remove-todo') || e.target.closest('.remove-todo')) {
                    const todoRow = e.target.closest('tr');
                    todoRow.remove();
                    this.reindexTodos();
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
                    }
                }
            });
        }
    },

    initRichTextEditor: function() {
        // Initialize rich text editor for description if available
        const descriptionField = document.querySelector('textarea[name="description"]');
        if (descriptionField && typeof tinymce !== 'undefined') {
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
                toolbar: 'undo redo | formatselect | bold italic backcolor | \
                    alignleft aligncenter alignright alignjustify | \
                    bullist numlist outdent indent | removeformat | help',
                setup: function(editor) {
                    editor.on('change', function() {
                        editor.save();
                    });
                }
            });
        }
    },

    resetTaskForm: function() {
        const form = document.getElementById('taskForm');
        if (form) {
            form.reset();
            // Reset TinyMCE if it exists
            if (typeof tinymce !== 'undefined') {
                const editor = tinymce.get('description');
                if (editor) {
                    editor.setContent('');
                }
            }
            // Reset status and priority colors
            const selects = form.querySelectorAll('select[name="status"], select[name="priority"]');
            selects.forEach(select => this.updateSelectColor(select));
            
            // Clear todos
            const todoList = document.getElementById('todoList');
            if (todoList) {
                todoList.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-muted">
                            No todo items found.
                        </td>
                    </tr>
                `;
            }

            // Clear comments
            const commentsList = document.getElementById('commentsList');
            if (commentsList) {
                commentsList.innerHTML = '<div class="text-center text-muted">No comments yet</div>';
            }

            // Clear subtasks
            const subTasksList = document.getElementById('subTasksList');
            if (subTasksList) {
                subTasksList.innerHTML = '';
            }
        }
    },

    handleFormSubmit: function(e) {
        e.preventDefault();
        
        // Update TinyMCE content before submitting
        if (typeof tinymce !== 'undefined') {
            const editor = tinymce.get('description');
            if (editor) {
                editor.save(); // This will update the textarea with the current content
            }
        }

        // Submit the form
        e.target.submit();
    },

    addComment: function() {
        const commentInput = document.getElementById('commentInput');
        const content = commentInput.value.trim();
        const taskId = window.taskModule.taskId;

        if (!content) {
            toastr.error('Comment cannot be empty');
            return;
        }

        fetch(`/projects/task/${taskId}/comment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({ content })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastr.success(data.message);
                commentInput.value = '';
                // Reload comments
                this.loadComments(taskId);
            } else {
                toastr.error(data.message || 'Error adding comment');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastr.error('Error adding comment');
        });
    },

    loadComments: function(taskId) {
        fetch(`/projects/task/${taskId}/comments`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const commentsList = document.getElementById('commentsList');
                    if (commentsList) {
                        commentsList.innerHTML = data.comments.map(comment => `
                            <div class="direct-chat-msg">
                                <div class="direct-chat-infos clearfix">
                                    <span class="direct-chat-name float-left">${comment.user}</span>
                                    <span class="direct-chat-timestamp float-right">${comment.created_at}</span>
                                </div>
                                <div class="direct-chat-text">${comment.content}</div>
                            </div>
                        `).join('') || '<div class="text-center text-muted">No comments yet</div>';
                    }
                } else {
                    toastr.error(data.message || 'Error loading comments');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                toastr.error('Error loading comments');
            });
    },

    addTodoItem: function() {
        const todoList = document.getElementById('todoList');
        const noTodosRow = todoList.querySelector('tr td[colspan]');
        if (noTodosRow) {
            noTodosRow.remove();
        }

        const index = todoList.getElementsByTagName('tr').length;
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
    },

    reindexTodos: function() {
        const todoList = document.getElementById('todoList');
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
    TaskManager.init();
});
