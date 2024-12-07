// Utility functions
function showError(message) {
    toastr.error(message);
}

function showSuccess(message) {
    toastr.success(message);
}

function scrollToBottom() {
    const chatMessages = document.querySelector('.direct-chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Get CSRF token from meta tag
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

/* Edit modal functionality - commented out but kept for future reference
function createEditModal() {
    if (!document.getElementById('edit-comment-modal')) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'edit-comment-modal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Edit Comment</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <textarea id="edit-comment-content" class="form-control" rows="2" maxlength="300"></textarea>
                            <small class="text-muted float-end mt-1">
                                <span id="edit-char-count">0</span>/300 characters
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveEditedComment()">Save Changes</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Add character counter for edit modal
        document.getElementById('edit-comment-content').addEventListener('input', function() {
            document.getElementById('edit-char-count').textContent = this.value.length;
        });
    }
}
*/

// Comment operations
async function submitComment(event) {
    event.preventDefault();
    
    const textarea = document.getElementById('comment-message');
    const content = textarea.value.trim();
    
    if (!content) {
        return;
    }

    try {
        const response = await fetch(`/projects/${projectId}/comment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify({
                content: content
            })
        });

        if (!response.ok) {
            throw new Error('Failed to post comment');
        }

        const result = await response.json();
        
        // Add the new comment to the chat
        const commentsContainer = document.querySelector('.direct-chat-messages');
        const newComment = createCommentElement(result.comment);
        commentsContainer.insertAdjacentHTML('beforeend', newComment);
        
        // Clear input and scroll to bottom
        textarea.value = '';
        document.getElementById('char-count').textContent = '0';
        scrollToBottom();
        
        showSuccess('Comment posted successfully');
    } catch (error) {
        showError('Error posting comment: ' + error.message);
    }
}

/* Edit/Delete functionality - commented out but kept for future reference
let currentEditingCommentId = null;

async function editComment(commentId) {
    try {
        createEditModal();
        currentEditingCommentId = commentId;
        
        const commentElement = document.querySelector(`#comment-${commentId} .direct-chat-text`);
        const currentContent = commentElement.textContent.trim();
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('edit-comment-modal'));
        modal.show();
        
        // Set content and update character count
        const editTextarea = document.getElementById('edit-comment-content');
        editTextarea.value = currentContent;
        document.getElementById('edit-char-count').textContent = currentContent.length;
    } catch (error) {
        showError('Error preparing comment edit: ' + error.message);
    }
}

async function saveEditedComment() {
    if (!currentEditingCommentId) return;

    try {
        const editTextarea = document.getElementById('edit-comment-content');
        const newContent = editTextarea.value.trim();
        
        const response = await fetch(`/projects/comment/${currentEditingCommentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': getCsrfToken()
            },
            body: JSON.stringify({
                content: newContent
            })
        });

        if (!response.ok) {
            throw new Error('Failed to update comment');
        }

        // Update comment content
        const commentElement = document.querySelector(`#comment-${currentEditingCommentId} .direct-chat-text`);
        commentElement.textContent = newContent;
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('edit-comment-modal')).hide();
        
        showSuccess('Comment updated successfully');
    } catch (error) {
        showError('Error updating comment: ' + error.message);
    }
}

async function deleteComment(commentId) {
    if (!confirm('Are you sure you want to delete this comment?')) {
        return;
    }

    try {
        const response = await fetch(`/projects/comment/${commentId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': getCsrfToken()
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete comment');
        }

        // Remove the comment element
        const commentElement = document.querySelector(`#comment-${commentId}`);
        if (commentElement) {
            commentElement.remove();
        }
        
        showSuccess('Comment deleted successfully');
    } catch (error) {
        showError('Error deleting comment: ' + error.message);
    }
}
*/

function createCommentElement(comment) {
    const isCurrentUser = comment.user_id === currentUserId;
    const timestamp = new Date(comment.created_at).toLocaleString();
    const avatarPath = comment.user_avatar.startsWith('/') ? comment.user_avatar : `/static/${comment.user_avatar}`;
    
    return `
    <div class="direct-chat-msg ${isCurrentUser ? 'right' : ''}" id="comment-${comment.id}">
        <div class="direct-chat-infos clearfix">
            <span class="direct-chat-name float-${isCurrentUser ? 'right' : 'left'}">
                ${comment.user}
            </span>
            <span class="direct-chat-timestamp float-${isCurrentUser ? 'left' : 'right'}">
                ${timestamp}
            </span>
        </div>
        <img class="direct-chat-img" src="${avatarPath}" alt="message user image">
        <div class="direct-chat-text">
            ${comment.content}
        </div>
    </div>
    `;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Scroll to bottom of chat on load
    scrollToBottom();
    
    // Initialize toastr if not already initialized
    if (typeof toastr !== 'undefined' && !toastr.options) {
        toastr.options = {
            closeButton: true,
            progressBar: true,
            positionClass: "toast-top-right",
            timeOut: 3000
        };
    }
});
