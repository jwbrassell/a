document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;
    const navbar = document.querySelector('.main-header.navbar');
    const icon = darkModeToggle.querySelector('i');
    const html = document.documentElement;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    function enableDarkMode() {
        body.classList.add('dark-mode');
        navbar.classList.remove('navbar-light', 'navbar-white');
        navbar.classList.add('navbar-dark', 'bg-dark');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        html.setAttribute('data-bs-theme', 'dark');
    }

    function disableDarkMode() {
        body.classList.remove('dark-mode');
        navbar.classList.remove('navbar-dark', 'bg-dark');
        navbar.classList.add('navbar-light', 'navbar-white');
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        html.setAttribute('data-bs-theme', 'light');
    }
    
    darkModeToggle.addEventListener('click', function(e) {
        e.preventDefault();
        const newTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
        
        // Apply theme change immediately
        if (newTheme === 'dark') {
            enableDarkMode();
        } else {
            disableDarkMode();
        }
        
        // Update theme via API
        fetch('/profile/preferences/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ theme: newTheme })
        })
        .then(response => {
            if (!response.ok) {
                // Revert theme if server update fails
                if (newTheme === 'dark') {
                    disableDarkMode();
                } else {
                    enableDarkMode();
                }
                throw new Error('Theme update failed');
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error updating theme:', error);
            // Show error message to user
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
            });
            Toast.fire({
                icon: 'error',
                title: 'Failed to save theme preference'
            });
        });
    });

    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.classList.add('fade-out');
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
});
