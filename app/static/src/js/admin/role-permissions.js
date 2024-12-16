$(document).ready(function() {
    // Permission search functionality
    $('#permission-search').on('input', function() {
        const search = $(this).val().toLowerCase();
        
        // Hide/show permission items based on search
        $('.permission-item').each(function() {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(search));
        });
        
        // Show/hide categories based on visible permissions
        $('.permission-category').each(function() {
            const hasVisiblePerms = $(this).find('.permission-item:visible').length > 0;
            $(this).toggle(hasVisiblePerms);
        });
    });

    // Category select/deselect all
    $('.select-all-category').click(function() {
        const category = $(this).data('category');
        const checkboxes = $(this).closest('.permission-category')
                                 .find('.permission-checkbox');
        
        checkboxes.prop('checked', true);
        checkboxes.trigger('change');
        
        // Visual feedback
        toastr.success('All permissions selected for ' + category);
    });

    $('.deselect-all-category').click(function() {
        const category = $(this).data('category');
        const checkboxes = $(this).closest('.permission-category')
                                 .find('.permission-checkbox');
        
        checkboxes.prop('checked', false);
        checkboxes.trigger('change');
        
        // Visual feedback
        toastr.info('All permissions deselected for ' + category);
    });

    // Expand/Collapse all categories
    $('#expand-all').click(function() {
        $('.permission-category .card-body').collapse('show');
        $(this).blur(); // Remove focus
    });

    $('#collapse-all').click(function() {
        $('.permission-category .card-body').collapse('hide');
        $(this).blur(); // Remove focus
    });

    // Permission checkbox change handler
    $('.permission-checkbox').change(function() {
        const permissionName = $(this).next('label').text().trim();
        const isChecked = $(this).prop('checked');
        
        // Update inherited permissions preview if needed
        updateInheritedPermissionsPreview();
        
        // Visual feedback
        if (isChecked) {
            toastr.success('Added permission: ' + permissionName);
        } else {
            toastr.info('Removed permission: ' + permissionName);
        }
    });

    // Function to update inherited permissions preview
    function updateInheritedPermissionsPreview() {
        const parentId = $('#parent_id').val();
        if (!parentId) {
            $('.inheritance-preview').hide();
            return;
        }

        $.get('/admin/roles/' + parentId + '/permissions', function(permissions) {
            if (permissions && permissions.length > 0) {
                let html = permissions.map(perm => 
                    `<span class="badge badge-info mr-2 mb-2">${perm.name}</span>`
                ).join('');
                
                $('.inherited-permissions').html(html);
                $('.inheritance-preview').show();
            } else {
                $('.inheritance-preview').hide();
            }
        });
    }

    // Initialize permission categories as collapsed on mobile
    if (window.innerWidth < 768) {
        $('.permission-category .card-body').collapse('hide');
    }

    // Search highlight functionality
    let searchTimeout;
    $('#permission-search').on('input', function() {
        clearTimeout(searchTimeout);
        const search = $(this).val().toLowerCase();
        
        searchTimeout = setTimeout(function() {
            $('.permission-item').each(function() {
                const $item = $(this);
                const text = $item.text().toLowerCase();
                
                if (search && text.includes(search)) {
                    const regex = new RegExp('(' + search + ')', 'gi');
                    const highlightedText = $item.find('label').text()
                        .replace(regex, '<mark>$1</mark>');
                    $item.find('label').html(highlightedText);
                } else {
                    $item.find('label').html(
                        $item.find('label').text()
                    );
                }
            });
        }, 200);
    });

    // Permission category collapse state persistence
    $('.permission-category .card-header').click(function() {
        const $category = $(this).closest('.permission-category');
        const $body = $category.find('.card-body');
        const categoryId = $category.data('category-id');
        
        $body.collapse('toggle');
        
        // Store collapse state
        const collapsedCategories = JSON.parse(
            localStorage.getItem('collapsedPermissionCategories') || '[]'
        );
        
        const index = collapsedCategories.indexOf(categoryId);
        if ($body.hasClass('show')) {
            if (index > -1) {
                collapsedCategories.splice(index, 1);
            }
        } else {
            if (index === -1) {
                collapsedCategories.push(categoryId);
            }
        }
        
        localStorage.setItem(
            'collapsedPermissionCategories',
            JSON.stringify(collapsedCategories)
        );
    });

    // Restore category collapse states
    const collapsedCategories = JSON.parse(
        localStorage.getItem('collapsedPermissionCategories') || '[]'
    );
    
    collapsedCategories.forEach(categoryId => {
        $('.permission-category[data-category-id="' + categoryId + '"]')
            .find('.card-body')
            .collapse('hide');
    });
});
