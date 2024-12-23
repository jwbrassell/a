$(document).ready(function() {
    // Initialize role hierarchy visualization
    let roleTreeData = null;
    
    // Function to update role tree visualization
    function updateRoleTree() {
        const selectedParentId = $('#parent_id').val();
        
        $.get('/admin/roles/tree', function(data) {
            roleTreeData = data;
            renderRoleTree(roleTreeData);
        });

        function renderRoleTree(roles, level = 0) {
            let html = '';
            roles.forEach(role => {
                const padding = level * 20;
                const isSelected = role.id == selectedParentId;
                const canBeParent = canBeParentRole(role);
                
                html += `
                    <div class="role-tree-item ${isSelected ? 'selected' : ''} 
                              ${canBeParent ? '' : 'disabled'}"
                         style="margin-left: ${padding}px"
                         data-role-id="${role.id}">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <i class="fas ${role.icon} mr-2"></i>
                                <span class="role-name">${role.name}</span>
                            </div>
                            <div>
                                <span class="badge badge-info" title="Users">
                                    <i class="fas fa-users mr-1"></i>${role.user_count}
                                </span>
                                <span class="badge badge-secondary" title="Permissions">
                                    <i class="fas fa-key mr-1"></i>${role.permission_count}
                                </span>
                            </div>
                        </div>
                    </div>
                `;
                
                if (role.children && role.children.length > 0) {
                    html += renderRoleTree(role.children, level + 1);
                }
            });
            return html;
        }

        // Update the tree visualization
        $('#role-tree').html(renderRoleTree(roleTreeData));
        
        // Initialize tooltips
        $('#role-tree [title]').tooltip();
    }

    // Function to check if a role can be a parent
    function canBeParentRole(role) {
        const currentRoleId = $('#role-form').data('role-id');
        if (role.id === currentRoleId) return false;
        
        // Check if the role is a descendant of the current role
        function isDescendant(parent) {
            if (!parent.children) return false;
            return parent.children.some(child => {
                if (child.id === currentRoleId) return true;
                return isDescendant(child);
            });
        }
        
        return !isDescendant(role);
    }

    // Handle parent role selection change
    $('#parent_id').change(function() {
        const selectedId = $(this).val();
        updateRoleTree();
        
        if (selectedId) {
            // Show inheritance preview
            $.get('/admin/roles/' + selectedId + '/permissions', function(permissions) {
                if (permissions && permissions.length > 0) {
                    let html = `
                        <div class="inheritance-preview p-3 mt-3">
                            <h6><i class="fas fa-arrow-up mr-2"></i>Inherited Permissions</h6>
                            <p class="mb-2 text-muted">
                                The following permissions will be inherited:
                            </p>
                            <div class="inherited-permissions">
                                ${permissions.map(perm => 
                                    `<span class="badge badge-info mr-2 mb-2">${perm.name}</span>`
                                ).join('')}
                            </div>
                        </div>
                    `;
                    $('#inheritance-preview-container').html(html).show();
                } else {
                    $('#inheritance-preview-container').hide();
                }
            });
        } else {
            $('#inheritance-preview-container').hide();
        }
    });

    // Make role tree items clickable
    $(document).on('click', '.role-tree-item:not(.disabled)', function() {
        const roleId = $(this).data('role-id');
        $('#parent_id').val(roleId).trigger('change');
    });

    // Initialize hierarchy visualization
    updateRoleTree();

    // Handle window resize
    let resizeTimeout;
    $(window).resize(function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(updateRoleTree, 250);
    });

    // Add role tree search functionality
    $('#role-tree-search').on('input', function() {
        const search = $(this).val().toLowerCase();
        
        $('.role-tree-item').each(function() {
            const roleName = $(this).find('.role-name').text().toLowerCase();
            const matches = roleName.includes(search);
            $(this).toggle(matches);
            
            // If this item matches, also show its ancestors
            if (matches) {
                let current = $(this);
                while (current.length) {
                    current.show();
                    current = current.prevAll('.role-tree-item').first();
                }
            }
        });
    });

    // Add expand/collapse all functionality for role tree
    $('#expand-role-tree').click(function() {
        $('.role-tree-item').show();
        $(this).blur();
    });

    $('#collapse-role-tree').click(function() {
        // Hide all except top-level items
        $('.role-tree-item').each(function() {
            if (parseInt($(this).css('margin-left')) > 0) {
                $(this).hide();
            }
        });
        $(this).blur();
    });

    // Add role tree context menu
    $.contextMenu({
        selector: '.role-tree-item:not(.disabled)',
        items: {
            select: {
                name: "Select as Parent",
                icon: "fas fa-check",
                callback: function(key, opt) {
                    const roleId = $(this).data('role-id');
                    $('#parent_id').val(roleId).trigger('change');
                }
            },
            view: {
                name: "View Role Details",
                icon: "fas fa-eye",
                callback: function(key, opt) {
                    const roleId = $(this).data('role-id');
                    window.location.href = '/admin/roles/' + roleId + '/edit';
                }
            }
        }
    });
});
