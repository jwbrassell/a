// Theme Management Class
class ThemeManager {
    constructor() {
        this.darkModeToggle = document.getElementById('darkModeToggle');
        this.profileThemeToggle = document.getElementById('profileThemeToggle');
        this.body = document.body;
        this.navbar = document.querySelector('.main-header.navbar');
        this.icon = this.darkModeToggle?.querySelector('i');
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        this.isLoggedIn = this.csrfToken && document.querySelector('.nav-item.dropdown') !== null;
        
        // Performance optimization: Store DOM queries
        this.htmlElement = document.documentElement;
        
        // Debounce timer for theme changes
        this.themeChangeTimer = null;
        
        this.initialize();
    }
    
    enableDarkMode() {
        // Batch DOM operations
        requestAnimationFrame(() => {
            this.body.classList.add('dark-mode');
            this.navbar.classList.remove('navbar-light', 'navbar-white');
            this.navbar.classList.add('navbar-dark', 'bg-dark');
            this.htmlElement.setAttribute('data-bs-theme', 'dark');
            
            if (this.icon) {
                this.icon.classList.remove('fa-moon');
                this.icon.classList.add('fa-sun');
            }
            
            if (this.profileThemeToggle) {
                this.profileThemeToggle.checked = true;
            }
        });
    }

    disableDarkMode() {
        // Batch DOM operations
        requestAnimationFrame(() => {
            this.body.classList.remove('dark-mode');
            this.navbar.classList.remove('navbar-dark', 'bg-dark');
            this.navbar.classList.add('navbar-light', 'navbar-white');
            this.htmlElement.setAttribute('data-bs-theme', 'light');
            
            if (this.icon) {
                this.icon.classList.remove('fa-sun');
                this.icon.classList.add('fa-moon');
            }
            
            if (this.profileThemeToggle) {
                this.profileThemeToggle.checked = false;
            }
        });
    }

    async setTheme(theme, savePreference = true) {
        // Debounce theme changes
        clearTimeout(this.themeChangeTimer);
        this.themeChangeTimer = setTimeout(async () => {
            theme === 'dark' ? this.enableDarkMode() : this.disableDarkMode();

            if (savePreference) {
                try {
                    if (this.isLoggedIn) {
                        const response = await fetch('/profile/preferences/theme', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': this.csrfToken
                            },
                            body: JSON.stringify({ theme })
                        });

                        if (!response.ok) {
                            throw new Error('Theme update failed');
                        }
                        
                        await response.json();
                    } else {
                        // Enhanced cookie with SameSite attribute
                        document.cookie = `theme=${theme};path=/;max-age=31536000;SameSite=Lax`;
                    }
                } catch (error) {
                    console.error('Error updating theme:', error);
                    
                    // Revert theme change
                    theme === 'dark' ? this.disableDarkMode() : this.enableDarkMode();
                    
                    // Show error toast
                    this.showToast({
                        icon: 'error',
                        title: error.message === 'Failed to fetch' 
                            ? 'Could not connect to server' 
                            : 'Failed to save theme preference'
                    });
                }
            }
        }, 150); // Debounce delay
    }

    showToast(options) {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer);
                toast.addEventListener('mouseleave', Swal.resumeTimer);
            }
        });
        Toast.fire(options);
    }

    initialize() {
        // Get theme from data-bs-theme attribute
        const htmlTheme = this.htmlElement.getAttribute('data-bs-theme');
        
        if (this.isLoggedIn) {
            this.setTheme(htmlTheme || 'light', false);
        } else {
            const savedTheme = document.cookie.split('; ')
                .find(row => row.startsWith('theme='))
                ?.split('=')[1];
            
            if (savedTheme) {
                this.setTheme(savedTheme, false);
            } else {
                this.setTheme('light', false);
            }
        }

        // Event Listeners
        if (this.darkModeToggle) {
            this.darkModeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                const newTheme = this.body.classList.contains('dark-mode') ? 'light' : 'dark';
                this.setTheme(newTheme);
            });
        }

        if (this.profileThemeToggle) {
            this.profileThemeToggle.addEventListener('change', (e) => {
                const newTheme = e.target.checked ? 'dark' : 'light';
                this.setTheme(newTheme);
            });
        }

        // Initialize flash messages
        this.initializeFlashMessages();
    }

    initializeFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.classList.add('fade-out');
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 500);
            }, 5000);
        });
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});
