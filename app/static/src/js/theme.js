document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const profileThemeToggle = document.getElementById('profileThemeToggle');
    const body = document.body;
    const navbar = document.querySelector('.main-header.navbar');
    const icon = darkModeToggle.querySelector('i');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const isLoggedIn = document.querySelector('meta[name="csrf-token"]').getAttribute('content') !== '' && 
                      document.querySelector('.nav-item.dropdown') !== null;
    
    function enableDarkMode() {
        // Update AdminLTE classes
        body.classList.add('dark-mode');
        navbar.classList.remove('navbar-light', 'navbar-white');
        navbar.classList.add('navbar-dark', 'bg-dark');
        
        // Update Bootstrap theme
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        
        // Update icon
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
        
        // Update profile toggle if it exists
        if (profileThemeToggle) {
            profileThemeToggle.checked = true;
        }
    }

    function disableDarkMode() {
        // Update AdminLTE classes
        body.classList.remove('dark-mode');
        navbar.classList.remove('navbar-dark', 'bg-dark');
        navbar.classList.add('navbar-light', 'navbar-white');
        
        // Update Bootstrap theme
        document.documentElement.setAttribute('data-bs-theme', 'light');
        
        // Update icon
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
        
        // Update profile toggle if it exists
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
                    // Revert the theme change
                    if (theme === 'dark') {
                        disableDarkMode();
                    } else {
                        enableDarkMode();
                    }
                    // Show error message
                    const Toast = Swal.mixin({
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 3000,
                        timerProgressBar: true,
                        didOpen: (toast) => {
                            toast.addEventListener('mouseenter', Swal.stopTimer)
                            toast.addEventListener('mouseleave', Swal.resumeTimer)
                        }
                    });
                    Toast.fire({
                        icon: 'error',
                        title: error.message === 'Failed to fetch' 
                            ? 'Could not connect to server' 
                            : 'Failed to save theme preference'
                    });
                });
            } else {
                // Store theme in cookie for non-logged in users
                document.cookie = `theme=${theme};path=/;max-age=31536000`;
            }
        }
    }

    // Load initial theme
    function initializeTheme() {
        // Get theme from data-bs-theme attribute
        const htmlTheme = document.documentElement.getAttribute('data-bs-theme');
        
        if (isLoggedIn) {
            // For logged in users, use server preference
            setTheme(htmlTheme || 'light', false);
        } else {
            // For non-logged in users, prefer cookie over default
            const savedTheme = document.cookie.split('; ').find(row => row.startsWith('theme='))?.split('=')[1];
            if (savedTheme) {
                setTheme(savedTheme, false);
            } else {
                setTheme('light', false);
                localStorage.setItem('theme', 'light');
            }
        }
    }

    // Initialize theme after DOM is loaded
    initializeTheme();
    
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
