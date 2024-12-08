// Task Management Module
const TaskManager = {
    init: function() {
        this.bindEvents();
        this.initTodoHandlers();
        this.initRichTextEditor();
        this.initStatusPriorityHandlers();
    },

    bindEvents: function() {
        // Form submission is handled normally by the browser
        // We only need to ensure tinymce content is synced
        const taskForm = document.getElementById('taskForm');
        if (taskForm) {
            taskForm.addEventListener('submit', this.handleFormSubmit.bind(this));
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
                    bullist numlist outdent indent | removeformat | help'
            });
        }
    },

    getStatusOptionsTemplate: function() {
        const statusSelect = document.querySelector('select[name="status"]');
        return Array.from(statusSelect.options)
            .map(option => `<option value="${option.value}" data-color="${option.dataset.color}">${option.text}</option>`)
            .join('');
    },

    getPriorityOptionsTemplate: function() {
        const prioritySelect = document.querySelector('select[name="priority"]');
        return Array.from(prioritySelect.options)
            .map(option => `<option value="${option.value}" data-color="${option.dataset.color}">${option.text}</option>`)
            .join('');
    },

    getUserOptionsTemplate: function() {
        const userSelect = document.querySelector('select[name="assigned_to_id"]');
        return Array.from(userSelect.options)
            .map(option => `<option value="${option.value}">${option.text}</option>`)
            .join('');
    },

    addTodoItem: function() {
        const todoList = document.getElementById('todoList');
        const index = todoList.getElementsByTagName('tr').length;
        const template = `
            <tr>
                <td>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input todo-checkbox" 
                               id="todoCheck_new_${index}" 
                               name="todos[${index}][completed]">
                        <label class="form-check-label" for="todoCheck_new_${index}"></label>
                    </div>
                </td>
                <td>
                    <input type="text" class="form-control todo-description bg-dark text-light border-secondary" 
                           name="todos[${index}][description]">
                </td>
                <td>
                    <input type="date" class="form-control todo-due-date bg-dark text-light border-secondary"
                           name="todos[${index}][due_date]">
                </td>
                <td>
                    <button type="button" class="btn btn-danger btn-sm remove-todo">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        todoList.insertAdjacentHTML('beforeend', template);
    },

    addSubTask: function() {
        const subTasksList = document.getElementById('subTasksList');
        const index = document.querySelectorAll('.subtask-item').length;
        const template = `
            <div class="subtask-item mb-3">
                <div class="card">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group mb-2">
                                    <label class="form-label">Name</label>
                                    <input type="text" class="form-control" name="subtasks[${index}][name]">
                                </div>
                                <div class="form-group mb-2">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="subtasks[${index}][description]" rows="2"></textarea>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group mb-2">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="subtasks[${index}][status]">
                                        ${this.getStatusOptionsTemplate()}
                                    </select>
                                </div>
                                <div class="form-group mb-2">
                                    <label class="form-label">Priority</label>
                                    <select class="form-select" name="subtasks[${index}][priority]">
                                        ${this.getPriorityOptionsTemplate()}
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Lead</label>
                                    <select class="form-select" name="subtasks[${index}][assigned_to_id]">
                                        ${this.getUserOptionsTemplate()}
                                    </select>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-danger btn-sm mt-2 remove-subtask">
                            <i class="fas fa-trash"></i> Remove
                        </button>
                    </div>
                </div>
            </div>
        `;
        subTasksList.insertAdjacentHTML('beforeend', template);

        // Initialize status/priority colors for new selects
        const newSubtask = subTasksList.lastElementChild;
        const newSelects = newSubtask.querySelectorAll('select[name*="[status]"], select[name*="[priority]"]');
        newSelects.forEach(select => {
            this.updateSelectColor(select);
            select.addEventListener('change', () => this.updateSelectColor(select));
        });
    },

    reindexTodos: function() {
        const todoList = document.getElementById('todoList');
        const todos = todoList.getElementsByTagName('tr');
        Array.from(todos).forEach((todo, index) => {
            const checkbox = todo.querySelector('.todo-checkbox');
            const description = todo.querySelector('.todo-description');
            const dueDate = todo.querySelector('.todo-due-date');

            if (checkbox) checkbox.name = `todos[${index}][completed]`;
            if (description) description.name = `todos[${index}][description]`;
            if (dueDate) dueDate.name = `todos[${index}][due_date]`;
        });
    },

    handleFormSubmit: function(e) {
        // Only sync tinymce content before form submission
        if (typeof tinymce !== 'undefined') {
            const editor = tinymce.get('description');
            if (editor) {
                editor.save(); // This syncs the editor content to the textarea
            }
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    TaskManager.init();

    // Add Sub Task button handler
    const addSubTaskBtn = document.getElementById('addSubTaskBtn');
    if (addSubTaskBtn) {
        addSubTaskBtn.addEventListener('click', () => TaskManager.addSubTask());
    }

    // Remove Sub Task handler
    const subTasksList = document.getElementById('subTasksList');
    if (subTasksList) {
        subTasksList.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-subtask') || e.target.closest('.remove-subtask')) {
                const subtaskItem = e.target.closest('.subtask-item');
                subtaskItem.remove();
            }
        });
    }
});
