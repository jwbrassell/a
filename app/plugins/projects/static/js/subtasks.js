// Sub Task Management

function loadSubTask(subtaskId, readonly = false) {
    fetch(`/projects/subtask/${subtaskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const subtask = data.subtask;
                console.log('Loaded subtask:', subtask);
                
                // Set modal title
                $('#modalTitle').text(readonly ? 'View Sub Task' : 'Edit Sub Task');
                
                // Store original values for change detection
                $('#subtaskForm').data('original-values', {
                    name: subtask.name || '',
                    summary: subtask.summary || '',
                    description: subtask.description || '',
                    status: subtask.status || '',
                    priority: subtask.priority || '',
                    assigned_to_id: subtask.assigned_to_id || '',
                    due_date: subtask.due_date || ''
                });
                
                populateSubtaskForm(subtask, data.statuses, data.priorities, data.users, readonly);
                
                // Store subtask ID for form submission
                $('#subtaskForm').data('subtask-id', subtaskId);
                
                // Load comments and history
                loadSubtaskComments(subtaskId);
                loadSubtaskHistory(subtaskId);
                
                // Show modal
                $('#subtaskModal').modal('show');
            } else {
                toastr.error(data.message || 'Error loading sub task');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastr.error('Error loading sub task');
        });
}

function populateSubtaskForm(subtask, statuses, priorities, users, readonly = false) {
    // Populate form fields
    $('#subtask-name').val(subtask.name || '');
    $('#subtask-summary').val(subtask.summary || '');
    
    // Set TinyMCE content after a short delay to ensure editor is initialized
    setTimeout(() => {
        const editor = tinymce.get('subtask-description');
        if (editor) {
            editor.setContent(subtask.description || '');
            editor.setMode(readonly ? 'readonly' : 'design');
        }
    }, 100);
    
    // Populate status dropdown
    const $statusSelect = $('#subtask-status');
    $statusSelect.empty().append('<option value="">Select Status</option>');
    statuses.forEach(status => {
        const selected = subtask.status === status.name ? 'selected' : '';
        $statusSelect.append(`<option value="${status.name}" data-color="${status.color}" ${selected}>${status.name}</option>`);
    });
    updateSelectStyling($statusSelect);
    
    // Populate priority dropdown
    const $prioritySelect = $('#subtask-priority');
    $prioritySelect.empty().append('<option value="">Select Priority</option>');
    priorities.forEach(priority => {
        const selected = subtask.priority === priority.name ? 'selected' : '';
        $prioritySelect.append(`<option value="${priority.name}" data-color="${priority.color}" ${selected}>${priority.name}</option>`);
    });
    updateSelectStyling($prioritySelect);
    
    // Populate users dropdown
    const $assignedSelect = $('#subtask-assigned');
    $assignedSelect.empty().append('<option value="">Select User</option>');
    users.forEach(user => {
        const selected = subtask.assigned_to_id === user.id ? 'selected' : '';
        $assignedSelect.append(`<option value="${user.id}" ${selected}>${user.username}</option>`);
    });
    
    // Set due date
    if (subtask.due_date) {
        const date = new Date(subtask.due_date);
        const formattedDate = date.toISOString().split('T')[0];
        $('#subtask-due-date').val(formattedDate);
    } else {
        $('#subtask-due-date').val('');
    }
    
    // Show/hide timestamps
    if (subtask.created_at) {
        $('#subtask-created-at').text(subtask.created_at);
        $('.created-at-field').show();
    } else {
        $('.created-at-field').hide();
    }
    if (subtask.updated_at) {
        $('#subtask-updated-at').text(subtask.updated_at);
        $('.updated-at-field').show();
    } else {
        $('.updated-at-field').hide();
    }
    
    // Set form state
    if (readonly) {
        $('#subtaskForm input, #subtaskForm select').prop('readonly', true);
        $('#subtaskForm button[type="submit"]').hide();
    } else {
        $('#subtaskForm input, #subtaskForm select').prop('readonly', false);
        $('#subtaskForm button[type="submit"]').show();
    }
}

function updateSelectStyling($select) {
    const selectedOption = $select.find('option:selected');
    if (selectedOption.val()) {
        const color = selectedOption.data('color');
        $select.css('background-color', `var(--bs-${color})`);
        $select.css('color', 'white');
        $select.attr('data-selected', 'true');
    } else {
        $select.css('background-color', '');
        $select.css('color', '');
        $select.removeAttr('data-selected');
    }
}

function addSubtaskToList(subtask, isTemp = false) {
    const subtaskId = isTemp ? `temp_${Math.random().toString(36).substr(2, 9)}` : subtask.id;
    const subtaskHtml = `
        <div class="subtask-item card bg-dark mb-3" data-subtask-id="${subtaskId}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="card-title mb-0">${subtask.name}</h5>
                    <div class="btn-group">
                        <button type="button" class="btn btn-sm btn-info view-subtask" title="View Sub Task">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-primary edit-subtask" title="Edit Sub Task">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-danger remove-subtask" title="Remove Sub Task">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <p class="card-text">${subtask.summary || ''}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        ${subtask.status ? `<span class="badge bg-${subtask.status_color || 'secondary'} me-2">${subtask.status}</span>` : ''}
                        ${subtask.priority ? `<span class="badge bg-${subtask.priority_color || 'secondary'} me-2">${subtask.priority}</span>` : ''}
                    </div>
                    <small class="text-muted">${subtask.due_date || 'No due date'}</small>
                </div>
            </div>
        </div>
    `;
    
    const $subTasksList = $('#subTasksList');
    $subTasksList.append(subtaskHtml);
}

function saveSubTask(event) {
    event.preventDefault();
    
    const subtaskId = $('#subtaskForm').data('subtask-id');
    const isNew = !subtaskId;
    const parentTaskId = taskModule.taskId;
    const isParentTemp = parentTaskId && parentTaskId.startsWith('temp_');
    
    // Get current form values
    const formData = {
        name: $('#subtask-name').val().trim(),
        summary: $('#subtask-summary').val().trim(),
        description: tinymce.get('subtask-description') ? tinymce.get('subtask-description').getContent() : '',
        status: $('#subtask-status').val(),
        priority: $('#subtask-priority').val(),
        assigned_to_id: $('#subtask-assigned').val() || null,
        due_date: $('#subtask-due-date').val() || null
    };

    // Validate required fields
    if (!formData.name) {
        toastr.error('Sub task name is required');
        return;
    }

    // If parent task is temporary, just add to UI
    if (isParentTemp) {
        addSubtaskToList({
            ...formData,
            status_color: $('#subtask-status option:selected').data('color'),
            priority_color: $('#subtask-priority option:selected').data('color')
        }, true);
        $('#subtaskModal').modal('hide');
        return;
    }

    // Otherwise, save to server
    const url = isNew ? `/projects/task/${parentTaskId}/subtask` : `/projects/subtask/${subtaskId}`;
    const method = isNew ? 'POST' : 'PUT';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            toastr.success(data.message || 'Sub task saved successfully');
            $('#subtaskModal').modal('hide');
            // Reload the page to show updated sub tasks
            window.location.reload();
        } else {
            toastr.error(data.message || 'Error saving sub task');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        toastr.error('Error saving sub task');
    });
}

function deleteSubTask(subtaskId) {
    // If it's a temporary subtask, just remove from UI
    if (subtaskId.startsWith('temp_')) {
        $(`[data-subtask-id="${subtaskId}"]`).remove();
        return;
    }

    fetch(`/projects/subtask/${subtaskId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastr.success(data.message || 'Sub task deleted successfully');
            // Reload the page to update sub tasks list
            window.location.reload();
        } else {
            toastr.error(data.message || 'Error deleting sub task');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        toastr.error('Error deleting sub task');
    });
}

function addSubtaskComment() {
    const subtaskId = $('#subtaskForm').data('subtask-id');
    const content = $('#subtaskCommentInput').val().trim();
    
    if (!content) {
        toastr.error('Comment cannot be empty');
        return;
    }

    // If parent task is temporary, just add to UI
    if (taskModule.taskId && taskModule.taskId.startsWith('temp_')) {
        const timestamp = new Date().toLocaleString();
        const commentHtml = `
            <div class="direct-chat-msg">
                <div class="direct-chat-infos clearfix">
                    <span class="direct-chat-name float-left">${window.currentUser || 'You'}</span>
                    <span class="direct-chat-timestamp float-right">${timestamp}</span>
                </div>
                <div class="direct-chat-text">${content}</div>
            </div>
        `;
        
        const $commentsList = $('#subtaskCommentsList');
        const noComments = $commentsList.find('.text-muted');
        if (noComments.length) {
            noComments.remove();
        }
        
        $commentsList.append(commentHtml);
        $('#subtaskCommentInput').val('');
        return;
    }
    
    fetch(`/projects/subtask/${subtaskId}/comment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        },
        body: JSON.stringify({ content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastr.success(data.message || 'Comment added successfully');
            $('#subtaskCommentInput').val('');
            loadSubtaskComments(subtaskId);
        } else {
            toastr.error(data.message || 'Error adding comment');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        toastr.error('Error adding comment');
    });
}

function loadSubtaskComments(subtaskId) {
    // Don't load comments for temporary subtasks
    if (subtaskId.startsWith('temp_')) {
        return;
    }

    fetch(`/projects/subtask/${subtaskId}/comments`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const commentsHtml = data.comments.map(comment => `
                    <div class="direct-chat-msg">
                        <div class="direct-chat-infos clearfix">
                            <span class="direct-chat-name float-left">${comment.user}</span>
                            <span class="direct-chat-timestamp float-right">${comment.created_at}</span>
                        </div>
                        <div class="direct-chat-text">${comment.content}</div>
                    </div>
                `).join('');
                
                $('#subtaskCommentsList').html(commentsHtml || '<div class="text-center text-muted">No comments yet</div>');
            } else {
                toastr.error(data.message || 'Error loading comments');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastr.error('Error loading comments');
        });
}

// Initialize event handlers
$(document).ready(function() {
    // Handle "Add Sub Task" button click
    $('#createSubTaskBtn').on('click', function() {
        // Reset form
        $('#subtaskForm')[0].reset();
        $('#subtaskForm').removeData('subtask-id');
        $('#subtaskForm').removeData('original-values');
        $('.created-at-field, .updated-at-field').hide();
        
        // Reset TinyMCE
        const editor = tinymce.get('subtask-description');
        if (editor) {
            editor.setContent('');
            editor.setMode('design');
        }
        
        // Reset status and priority styling
        $('#subtask-status, #subtask-priority').css({
            'background-color': '',
            'color': ''
        }).removeAttr('data-selected');
        
        // Enable form fields and show submit button
        $('#subtaskForm input, #subtaskForm select').prop('readonly', false);
        $('#subtaskForm button[type="submit"]').show();
        
        // Set modal title
        $('#modalTitle').text('Create Sub Task');
        
        // Show modal
        $('#subtaskModal').modal('show');
    });
    
    // Handle form submission
    $('#subtaskForm').on('submit', saveSubTask);
    
    // Handle status and priority changes
    $('#subtask-status, #subtask-priority').on('change', function() {
        updateSelectStyling($(this));
    });
    
    // Handle subtask actions using event delegation
    $('#subTasksList').on('click', '.remove-subtask', function() {
        const subtaskId = $(this).closest('.subtask-item').data('subtask-id');
        if (confirm('Are you sure you want to remove this sub task?')) {
            deleteSubTask(subtaskId);
        }
    });

    // Reset form when modal is hidden
    $('#subtaskModal').on('hidden.bs.modal', function() {
        $('#subtaskForm')[0].reset();
        $('#subtaskForm').removeData('subtask-id');
        $('#subtaskForm').removeData('original-values');
        $('.created-at-field, .updated-at-field').hide();
        $('#subtaskForm input, #subtaskForm select').prop('readonly', false);
        $('#subtaskForm button[type="submit"]').show();
        
        // Reset TinyMCE
        const editor = tinymce.get('subtask-description');
        if (editor) {
            editor.setContent('');
            editor.setMode('design');
        }
        
        // Reset status and priority styling
        $('#subtask-status, #subtask-priority').css({
            'background-color': '',
            'color': ''
        }).removeAttr('data-selected');

        // Clear comments
        $('#subtaskCommentsList').html('<div class="text-center text-muted">No comments yet</div>');
    });
});
