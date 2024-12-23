$(document).ready(function() {
    let iconsLoaded = false;
    
    // Initialize icon picker modal
    $('#icon-picker').click(function() {
        if (!iconsLoaded) {
            loadIcons();
        }
        $('#iconModal').modal('show');
    });

    // Load icons from server
    function loadIcons() {
        $('#icon-grid').html('<div class="text-center w-100"><i class="fas fa-spinner fa-spin fa-2x"></i></div>');
        
        $.get('/admin/icons', function(icons) {
            let html = '';
            icons.forEach(function(icon) {
                html += `
                    <div class="col-md-2 col-sm-3 col-4 text-center icon-item mb-3">
                        <div class="p-2 border rounded icon-select" 
                             data-icon="${icon}"
                             data-toggle="tooltip"
                             title="${icon}">
                            <i class="fas ${icon} fa-2x"></i>
                            <div class="small text-muted mt-1 icon-name">${icon.replace('fa-', '')}</div>
                        </div>
                    </div>
                `;
            });
            $('#icon-grid').html(html);
            
            // Initialize tooltips
            $('#icon-grid [data-toggle="tooltip"]').tooltip();
            
            iconsLoaded = true;
        }).fail(function() {
            $('#icon-grid').html(`
                <div class="alert alert-danger">
                    Failed to load icons. Please try again.
                </div>
            `);
        });
    }

    // Icon search functionality
    let searchTimeout;
    $('#icon-search').on('input', function() {
        clearTimeout(searchTimeout);
        const search = $(this).val().toLowerCase();
        
        searchTimeout = setTimeout(function() {
            $('.icon-item').each(function() {
                const icon = $(this).find('.icon-select').data('icon').toLowerCase();
                const matches = icon.includes(search);
                $(this).toggle(matches);
                
                // Highlight matching text
                if (matches && search) {
                    const iconName = $(this).find('.icon-name');
                    const text = iconName.text();
                    const regex = new RegExp('(' + search + ')', 'gi');
                    iconName.html(text.replace(regex, '<mark>$1</mark>'));
                } else {
                    const iconName = $(this).find('.icon-name');
                    iconName.html(iconName.text());
                }
            });
            
            // Show message if no results
            const visibleIcons = $('.icon-item:visible').length;
            if (visibleIcons === 0 && search) {
                if (!$('#no-icons-message').length) {
                    $('#icon-grid').append(`
                        <div id="no-icons-message" class="col-12 text-center mt-3">
                            <p class="text-muted">No icons found matching "${search}"</p>
                        </div>
                    `);
                }
            } else {
                $('#no-icons-message').remove();
            }
        }, 200);
    });

    // Icon selection handler
    $(document).on('click', '.icon-select', function() {
        const icon = $(this).data('icon');
        
        // Update form input and preview
        $('#icon').val(icon);
        $('#icon-preview').attr('class', 'fas ' + icon);
        
        // Visual feedback
        $(this).addClass('selected').siblings().removeClass('selected');
        setTimeout(() => {
            $('#iconModal').modal('hide');
            toastr.success('Icon updated');
        }, 200);
    });

    // Clear icon search when modal is hidden
    $('#iconModal').on('hidden.bs.modal', function() {
        $('#icon-search').val('').trigger('input');
    });

    // Keyboard navigation for icon grid
    let currentFocus = -1;
    
    $('#icon-search').on('keydown', function(e) {
        const visibleIcons = $('.icon-item:visible');
        
        switch(e.keyCode) {
            case 40: // Down arrow
                e.preventDefault();
                currentFocus = Math.min(currentFocus + 6, visibleIcons.length - 1);
                break;
            case 38: // Up arrow
                e.preventDefault();
                currentFocus = Math.max(currentFocus - 6, 0);
                break;
            case 39: // Right arrow
                e.preventDefault();
                currentFocus = Math.min(currentFocus + 1, visibleIcons.length - 1);
                break;
            case 37: // Left arrow
                e.preventDefault();
                currentFocus = Math.max(currentFocus - 1, 0);
                break;
            case 13: // Enter
                e.preventDefault();
                if (currentFocus >= 0) {
                    visibleIcons.eq(currentFocus).find('.icon-select').click();
                }
                return;
        }
        
        // Update focus visual
        $('.icon-select').removeClass('focused');
        if (currentFocus >= 0) {
            const focusedIcon = visibleIcons.eq(currentFocus).find('.icon-select');
            focusedIcon.addClass('focused');
            
            // Scroll into view if needed
            const container = $('#icon-grid');
            const iconTop = focusedIcon.offset().top;
            const containerTop = container.offset().top;
            const containerBottom = containerTop + container.height();
            
            if (iconTop < containerTop || iconTop > containerBottom) {
                focusedIcon[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest'
                });
            }
        }
    });

    // Add icon categories
    const categories = {
        'User Interface': ['fa-user', 'fa-users', 'fa-cog', 'fa-wrench', 'fa-gear'],
        'Navigation': ['fa-home', 'fa-compass', 'fa-map', 'fa-location-dot'],
        'Actions': ['fa-plus', 'fa-minus', 'fa-edit', 'fa-trash', 'fa-save'],
        'Communication': ['fa-envelope', 'fa-bell', 'fa-comment', 'fa-phone'],
        'Data': ['fa-database', 'fa-server', 'fa-cloud', 'fa-file'],
        'Security': ['fa-lock', 'fa-unlock', 'fa-shield', 'fa-key']
    };

    let categoryHtml = '<div class="mb-3"><select class="form-control" id="icon-category">';
    categoryHtml += '<option value="">All Categories</option>';
    for (let category in categories) {
        categoryHtml += `<option value="${category}">${category}</option>`;
    }
    categoryHtml += '</select></div>';

    $('#icon-search').before(categoryHtml);

    // Category filter handler
    $('#icon-category').change(function() {
        const category = $(this).val();
        if (!category) {
            $('.icon-item').show();
            return;
        }

        $('.icon-item').each(function() {
            const icon = $(this).find('.icon-select').data('icon');
            $(this).toggle(categories[category].includes(icon));
        });
    });

    // Add CSS for focused state
    $('<style>')
        .text(`
            .icon-select.focused {
                background-color: #e3f2fd;
                transform: scale(1.05);
                transition: all 0.2s;
            }
        `)
        .appendTo('head');
});
