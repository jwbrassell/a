/**
 * Navigation menu initialization and functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize category dropdowns
    document.querySelectorAll('.has-treeview').forEach(function(item) {
        const link = item.querySelector('.nav-link');
        const treeview = item.querySelector('.nav-treeview');
        const categoryId = item.dataset.categoryId;
        
        // Set initial state
        if (localStorage.getItem(`menu_${categoryId}`) === '1') {
            item.classList.add('menu-open');
            if (treeview) treeview.style.display = 'block';
        } else {
            if (treeview) treeview.style.display = 'none';
        }
        
        // Handle click events
        if (link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Toggle menu state
                item.classList.toggle('menu-open');
                
                // Animate submenu
                if (treeview) {
                    if (item.classList.contains('menu-open')) {
                        $(treeview).slideDown(300);
                        localStorage.setItem(`menu_${categoryId}`, '1');
                    } else {
                        $(treeview).slideUp(300);
                        localStorage.setItem(`menu_${categoryId}`, '0');
                    }
                }
            });
        }
    });
    
    // Mark active route and expand its category
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            
            // If in treeview, expand parent category
            const treeview = link.closest('.nav-treeview');
            if (treeview) {
                const categoryItem = treeview.closest('.has-treeview');
                if (categoryItem) {
                    categoryItem.classList.add('menu-open');
                    treeview.style.display = 'block';
                    categoryItem.querySelector('.nav-link').classList.add('active');
                    
                    // Store state
                    const categoryId = categoryItem.dataset.categoryId;
                    localStorage.setItem(`menu_${categoryId}`, '1');
                }
            }
        }
    });
});

// Add required CSS
const style = document.createElement('style');
style.textContent = `
    .nav-sidebar .nav-item > .nav-link {
        position: relative;
        cursor: pointer;
    }
    .nav-sidebar .nav-treeview {
        padding-left: 1rem;
        margin-left: 1.2rem;
        border-left: 1px solid rgba(255,255,255,0.1);
    }
    .nav-sidebar .nav-item.menu-open > .nav-link > p > .right,
    .nav-sidebar .nav-item.menu-open > .nav-link > .right {
        transform: rotate(-90deg);
    }
    .nav-sidebar .nav-link > p > .right,
    .nav-sidebar .nav-link > .right {
        transition: transform .3s ease-in-out;
    }
    .nav-sidebar .nav-treeview > .nav-item > .nav-link {
        position: relative;
    }
    .nav-sidebar .nav-treeview > .nav-item > .nav-link::before {
        content: '';
        position: absolute;
        left: -1.2rem;
        top: 50%;
        width: 0.8rem;
        height: 1px;
        background: rgba(255,255,255,0.1);
    }
`;
document.head.appendChild(style);
