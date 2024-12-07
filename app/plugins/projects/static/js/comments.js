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

// Create edit modal if it doesn't exist
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
                        <textarea id="edit-comment-content" class="form-control rich-text-editor"></textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveEditedComment()">Save Changes</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// Comment operations
async function submitComment(event) {
    event.preventDefault();
    
    const content = tinymce.get('comment-message').getContent().trim();
    
    if (!content) {
        return;
    }

    try {
        const response = await fetch('/projects/comments/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                project_id: projectId
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
        tinymce.get('comment-message').setContent('');
        scrollToBottom();
        
        showSuccess('Comment posted successfully');
    } catch (error) {
        showError('Error posting comment: ' + error.message);
    }
}

let currentEditingCommentId = null;

async function editComment(commentId) {
    try {
        createEditModal();
        currentEditingCommentId = commentId;
        
        const commentElement = document.querySelector(`#comment-${commentId} .direct-chat-text`);
        const currentContent = commentElement.innerHTML;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('edit-comment-modal'));
        modal.show();
        
        // Wait for TinyMCE to be ready
        setTimeout(() => {
            const editor = tinymce.get('edit-comment-content');
            if (editor) {
                editor.setContent(currentContent);
            }
        }, 100);
    } catch (error) {
        showError('Error preparing comment edit: ' + error.message);
    }
}

async function saveEditedComment() {
    if (!currentEditingCommentId) return;

    try {
        const newContent = tinymce.get('edit-comment-content').getContent();
        
        const response = await fetch(`/projects/comments/${currentEditingCommentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
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
        commentElement.innerHTML = newContent;
        
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
        const response = await fetch(`/projects/comments/${commentId}`, {
            method: 'DELETE'
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

function createCommentElement(comment) {
    const isCurrentUser = comment.user_id === currentUserId;
    const timestamp = new Date(comment.created_at).toLocaleString();
    
    return `
    <div class="direct-chat-msg ${isCurrentUser ? 'right' : ''}" id="comment-${comment.id}">
        <div class="direct-chat-infos clearfix">
            <span class="direct-chat-name float-${isCurrentUser ? 'right' : 'left'}">
                ${comment.user.name}
            </span>
            <span class="direct-chat-timestamp float-${isCurrentUser ? 'left' : 'right'}">
                ${timestamp}
            </span>
        </div>
        <img class="direct-chat-img" src="${comment.user.avatar_url}" alt="message user image">
        <div class="direct-chat-text rich-text-content">
            ${comment.content}
        </div>
        ${isCurrentUser ? `
        <div class="direct-chat-actions">
            <button class="btn btn-sm btn-link" onclick="editComment(${comment.id})">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-link text-danger" onclick="deleteComment(${comment.id})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        ` : ''}
    </div>
    `;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Create edit modal
    createEditModal();
    
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

    // Configure TinyMCE for comments with a simpler toolbar
    tinymce.init({
        selector: '#comment-message',
        menubar: false,
        plugins: 'link lists emoticons',
        toolbar: 'bold italic | bullist numlist | link emoticons',
        placeholder: 'Type your comment...',
        height: 120,
        skin: document.querySelector('html').dataset.bsTheme === 'dark' ? 'oxide-dark' : 'oxide',
        content_css: document.querySelector('html').dataset.bsTheme === 'dark' ? 'dark' : 'default'
    });
});
