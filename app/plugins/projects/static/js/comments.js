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

// Comment operations
function initializeComments() {
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', submitComment);
    }

    // Add character counter for comment textarea
    const commentTextarea = document.getElementById('comment-message');
    if (commentTextarea) {
        commentTextarea.addEventListener('input', function() {
            document.getElementById('char-count').textContent = this.value.length;
        });
    }

    // Scroll to bottom of chat on load
    scrollToBottom();
}

async function submitComment(event) {
    event.preventDefault();
    
    const textarea = document.getElementById('comment-message');
    const content = textarea.value.trim();
    
    if (!content) {
        return;
    }

    try {
        // Check if we're in a task or project context
        const projectId = window.projectId;
        const taskId = window.taskModule?.taskId;
        
        if (!projectId) {
            showError('Project ID not found');
            return;
        }

        // Prepare the request data
        const requestData = {
            content: content
        };

        // If we're in a task context, include the task_id
        if (taskId) {
            requestData.task_id = taskId;
        }

        const response = await fetch(`/projects/${projectId}/comment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Failed to post comment');
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

function createCommentElement(comment) {
    const currentUserId = window.currentUserId;
    const isCurrentUser = comment.user_id === parseInt(currentUserId);
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeComments);
