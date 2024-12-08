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
                data.statuses.forEach(status => {
                    const selected = subtask.status === status.name ? 'selected' : '';
                    $statusSelect.append(`<option value="${status.name}" data-color="${status.color}" ${selected}>${status.name}</option>`);
                });
                
                // Set status with badge styling
                const selectedStatus = $statusSelect.find('option:selected');
                if (selectedStatus.val()) {
                    const color = selectedStatus.data('color');
                    $statusSelect.css('background-color', `var(--bs-${color})`);
                    $statusSelect.css('color', 'white');
                    $statusSelect.attr('data-selected', 'true');
                } else {
                    $statusSelect.css('background-color', '');
                    $statusSelect.css('color', '');
                    $statusSelect.removeAttr('data-selected');
                }
                
                // Populate priority dropdown
                const $prioritySelect = $('#subtask-priority');
                $prioritySelect.empty().append('<option value="">Select Priority</option>');
                data.priorities.forEach(priority => {
                    const selected = subtask.priority === priority.name ? 'selected' : '';
                    $prioritySelect.append(`<option value="${priority.name}" data-color="${priority.color}" ${selected}>${priority.name}</option>`);
                });
                
                // Set priority with badge styling
                const selectedPriority = $prioritySelect.find('option:selected');
                if (selectedPriority.val()) {
                    const color = selectedPriority.data('color');
                    $prioritySelect.css('background-color', `var(--bs-${color})`);
                    $prioritySelect.css('color', 'white');
                    $prioritySelect.attr('data-selected', 'true');
                } else {
                    $prioritySelect.css('background-color', '');
                    $prioritySelect.css('color', '');
                    $prioritySelect.removeAttr('data-selected');
                }
                
                // Populate users dropdown
                const $assignedSelect = $('#subtask-assigned');
                $assignedSelect.empty().append('<option value="">Select User</option>');
                data.users.forEach(user => {
                    const selected = subtask.assigned_to_id === user.id ? 'selected' : '';
                    $assignedSelect.append(`<option value="${user.id}" ${selected}>${user.username}</option>`);
                });
                
                // Set due date - ensure proper date format
                if (subtask.due_date) {
                    // Convert date string to YYYY-MM-DD format
                    const date = new Date(subtask.due_date);
                    const formattedDate = date.toISOString().split('T')[0];
                    $('#subtask-due-date').val(formattedDate);
                } else {
                    $('#subtask-due-date').val('');
                }
                
                // Show timestamps if they exist
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

function loadSubtaskHistory(subtaskId) {
    fetch(`/projects/subtask/${subtaskId}/history`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const historyHtml = data.history.map(item => `
                    <tr>
                        <td>${item.created_at}</td>
                        <td>${item.user}</td>
                        <td>${item.action}</td>
                        <td>${formatHistoryDetails(item.details)}</td>
                    </tr>
                `).join('');
                
                $('#subtaskHistoryList').html(historyHtml || '<tr><td colspan="4" class="text-center">No history available</td></tr>');
            } else {
                toastr.error(data.message || 'Error loading history');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastr.error('Error loading history');
        });
}

function formatHistoryDetails(details) {
    if (typeof details === 'string') return details;
    
    let formattedDetails = [];
    for (let key in details) {
        if (typeof details[key] === 'object' && details[key] !== null) {
            const oldValue = details[key].old || 'None';
            const newValue = details[key].new || 'None';
            formattedDetails.push(`${key}: ${oldValue} → ${newValue}`);
        } else {
            formattedDetails.push(`${key}: ${details[key]}`);
        }
    }
    return formattedDetails.join('<br>');
}

function saveSubTask(event) {
    event.preventDefault();
    console.log('saveSubTask called');
    
    const subtaskId = $('#subtaskForm').data('subtask-id');
    const isNew = !subtaskId;
    
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

    console.log('Form data:', formData);

    // For new subtasks, just validate required fields
    if (isNew) {
        if (!formData.name) {
            toastr.error('Sub task name is required');
            return;
        }
    } else {
        // For existing subtasks, check if there are any changes
        const originalValues = $('#subtaskForm').data('original-values') || {};
        let hasChanges = false;
        
        // Debug log current values
        console.log('Current form values:', formData);
        console.log('Original values:', originalValues);
        
        // Compare each field
        for (const key in formData) {
            const originalValue = originalValues[key] || '';
            const currentValue = formData[key] || '';
            
            // Debug log comparison
            console.log(`Comparing ${key}:`, {
                original: originalValue,
                current: currentValue,
                changed: originalValue !== currentValue
            });
            
            if (originalValue !== currentValue) {
                hasChanges = true;
                break;
            }
        }
        
        if (!hasChanges) {
            toastr.info('No changes to save');
            return;
        }
    }
    
    const url = isNew ? `/projects/task/${taskModule.taskId}/subtask` : `/projects/subtask/${subtaskId}`;
    const method = isNew ? 'POST' : 'PUT';
    
    // Debug log the request
    console.log('Sending request:', {
        url,
        method,
        formData
    });
    
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
            // Clear input
            $('#subtaskCommentInput').val('');
            // Reload comments
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
    $('#subtaskForm').on('submit', function(e) {
        console.log('Form submitted');
        saveSubTask(e);
    });
    
    // Handle status and priority changes
    $('#subtask-status, #subtask-priority').on('change', function() {
        const $select = $(this);
        const selectedOption = $select.find('option:selected');
        const color = selectedOption.data('color');
        
        if (color && selectedOption.val()) {
            $select.css({
                'background-color': `var(--bs-${color})`,
                'color': 'white'
            });
            $select.attr('data-selected', 'true');
        } else {
            $select.css({
                'background-color': '',
                'color': ''
            });
            $select.removeAttr('data-selected');
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
    });
});
