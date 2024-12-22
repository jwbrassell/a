document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const profileThemeToggle = document.getElementById('profileThemeToggle');
    const body = document.body;
    const navbar = document.querySelector('.main-header.navbar');
    const icon = darkModeToggle.querySelector('i');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const isLoggedIn = document.querySelector('meta[name="csrf-token"]').getAttribute('content') !== '';
    
    function enableDarkMode() {
        body.classList.add('dark-mode');
        navbar.classList.remove('navbar-light', 'navbar-white');
        navbar.classList.add('navbar-dark', 'bg-dark');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        if (profileThemeToggle) {
            profileThemeToggle.checked = true;
        }
    }

    function disableDarkMode() {
        body.classList.remove('dark-mode');
        navbar.classList.remove('navbar-dark', 'bg-dark');
        navbar.classList.add('navbar-light', 'navbar-white');
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        document.documentElement.setAttribute('data-bs-theme', 'light');
        if (profileThemeToggle) {
            profileThemeToggle.checked = false;
        }
    }

    function setTheme(theme, savePreference = true) {
        if (theme === 'dark') {
            enableDarkMode();
        } else {
            disableDarkMode();
        }

        if (savePreference) {
            if (isLoggedIn) {
                // Save theme preference to server for logged in users
                fetch('/profile/preferences/theme', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ theme: theme })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Theme update failed');
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('Error updating theme:', error);
                    // Show error message
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
            } else {
                // Store theme in localStorage for non-logged in users
                localStorage.setItem('theme', theme);
            }
        }
    }

    // Load initial theme
    if (isLoggedIn) {
        // For logged in users, initial theme is set by server-side rendering
        const currentTheme = body.classList.contains('dark-mode') ? 'dark' : 'light';
        setTheme(currentTheme, false);
    } else {
        // For non-logged in users, check localStorage
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme, false);
    }
    
    // Handle navbar toggle click
    darkModeToggle.addEventListener('click', function(e) {
        e.preventDefault();
        const newTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
        setTheme(newTheme);
        // Sync profile toggle if it exists
        if (profileThemeToggle) {
            profileThemeToggle.checked = newTheme === 'dark';
        }
    });

    // Handle profile toggle change if it exists
    if (profileThemeToggle) {
        profileThemeToggle.addEventListener('change', function(e) {
            const newTheme = this.checked ? 'dark' : 'light';
            setTheme(newTheme);
            // No need to sync navbar toggle as it's handled in setTheme
        });
    }

    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.classList.add('fade-out');
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
});
