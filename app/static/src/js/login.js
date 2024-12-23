document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const submitButton = loginForm?.querySelector('button[type="submit"]');
    const submitLoader = loginForm?.querySelector('.submit-loader');

    if (loginForm && submitButton && submitLoader) {
        loginForm.addEventListener('submit', function(e) {
            // Disable button and show loader
            submitButton.disabled = true;
            submitLoader.style.display = 'block';
            
            // Store original button text
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '';

            // Re-enable button if form submission fails
            window.addEventListener('unhandledrejection', function() {
                submitButton.disabled = false;
                submitLoader.style.display = 'none';
                submitButton.innerHTML = originalText;
            }, { once: true });

            // Handle server-side validation errors
            if (document.querySelectorAll('.invalid-feedback').length > 0) {
                submitButton.disabled = false;
                submitLoader.style.display = 'none';
                submitButton.innerHTML = originalText;
            }
        });

        // Add input validation
        const inputs = loginForm.querySelectorAll('input[type="text"], input[type="password"]');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                // Remove error messages on input
                const feedback = this.parentElement.parentElement.querySelector('.invalid-feedback');
                if (feedback) {
                    feedback.style.display = 'none';
                }
                
                // Enable submit button if both fields have values
                const username = loginForm.querySelector('input[name="username"]').value;
                const password = loginForm.querySelector('input[name="password"]').value;
                submitButton.disabled = !(username && password);
            });

            // Prevent spaces in username and trim on blur
            if (input.name === 'username') {
                input.addEventListener('keypress', function(e) {
                    if (e.key === ' ') {
                        e.preventDefault();
                    }
                });
                
                input.addEventListener('blur', function() {
                    this.value = this.value.trim();
                });
            }
        });

        // Add enter key support
        loginForm.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !submitButton.disabled) {
                e.preventDefault();
                submitButton.click();
            }
        });

        // Focus username field on load
        const usernameInput = loginForm.querySelector('input[name="username"]');
        if (usernameInput) {
            usernameInput.focus();
        }
    }

    // Add password visibility toggle if needed
    const passwordInput = loginForm?.querySelector('input[name="password"]');
    if (passwordInput) {
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'btn btn-outline-secondary';
        toggleButton.innerHTML = '<i class="fas fa-eye" aria-hidden="true"></i>';
        toggleButton.setAttribute('aria-label', 'Toggle password visibility');
        
        const inputGroup = passwordInput.parentElement;
        inputGroup.appendChild(toggleButton);

        toggleButton.addEventListener('click', function() {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            this.innerHTML = `<i class="fas fa-eye${type === 'password' ? '' : '-slash'}" aria-hidden="true"></i>`;
        });
    }
});
