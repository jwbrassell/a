document.addEventListener('DOMContentLoaded', function() {
    // Role Management
    $('#createRole').click(function() {
        const form = $('#createRoleForm')[0];
        const formData = new FormData(form);
        
        fetch('/admin/role', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error creating role');
        });
    });

    $('.edit-role').click(function() {
        const id = $(this).data('id');
        
        fetch(`/admin/role/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const role = data.role;
                $('#edit_role_id').val(role.id);
                $('#edit_role_name').val(role.name);
                $('#edit_role_notes').val(role.notes);
                $('#edit_role_icon').val(role.icon).trigger('change');
                
                $('#editRoleModal').modal('show');
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading role data');
        });
    });

    $('#updateRole').click(function() {
        const id = $('#edit_role_id').val();
        const form = $('#editRoleForm')[0];
        const formData = new FormData(form);
        
        fetch(`/admin/role/${id}`, {
            method: 'PUT',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error updating role');
        });
    });

    $('.delete-role').click(function() {
        const id = $(this).data('id');
        const name = $(this).data('name');
        
        $('#deleteRoleText').text(`Role: ${name}`);
        $('#confirmDeleteRole').data('id', id);
        $('#deleteRoleModal').modal('show');
    });

    $('#confirmDeleteRole').click(function() {
        const id = $(this).data('id');
        
        fetch(`/admin/role/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting role');
        });
    });
});
