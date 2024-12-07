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

// Comment operations
async function submitComment(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('comment-message');
    const message = messageInput.value.trim();
    
    if (!message) {
        return;
    }

    try {
        const response = await fetch('/projects/comments/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: message,
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
        messageInput.value = '';
        scrollToBottom();
        
        showSuccess('Comment posted successfully');
    } catch (error) {
        showError('Error posting comment: ' + error.message);
    }
}

async function editComment(commentId) {
    try {
        const commentElement = document.querySelector(`#comment-${commentId} .direct-chat-text`);
        const currentContent = commentElement.textContent.trim();
        
        const newContent = prompt('Edit comment:', currentContent);
        
        if (!newContent || newContent === currentContent) {
            return;
        }

        const response = await fetch(`/projects/comments/${commentId}`, {
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

        commentElement.textContent = newContent;
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
        <div class="direct-chat-text">
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
