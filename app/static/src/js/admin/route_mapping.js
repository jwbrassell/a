document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2 for all selects except category selects
    $('.form-select:not(#category_id):not(#edit_category_id)').select2({
        theme: 'bootstrap4',
        width: '100%'
    });

    // Initialize category selects with tags enabled
    $('#category_id, #edit_category_id').select2({
        theme: 'bootstrap4',
        width: '100%',
        tags: true,
        allowClear: true,
        placeholder: 'Select or type a category'
    });

    // Special initialization for icon selects
    $('.icon-select').select2({
        theme: 'bootstrap4',
        width: '100%',
        templateResult: formatIcon,
        templateSelection: formatIcon
    });

    function formatIcon(icon) {
        if (!icon.id) return icon.text;
        return $('<span><i class="fas ' + icon.id + '"></i> ' + icon.text + '</span>');
    }

    // Category icon handling
    $('#category_id, #edit_category_id').on('change', function() {
        const selectedOption = $(this).select2('data')[0];
        if (selectedOption && !selectedOption.id.match(/^\d+$/)) {
            // New category, show icon selector
            $(this).closest('form').find('[name="category_icon"]').closest('.mb-3').show();
        } else {
            // Existing category, hide icon selector
            $(this).closest('form').find('[name="category_icon"]').closest('.mb-3').hide();
            
            // If it's an existing category, fetch its icon
            if (selectedOption && selectedOption.id) {
                fetch(`/admin/category/${selectedOption.id}/icon`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.icon) {
                            $(this).closest('form').find('[name="category_icon"]').val(data.icon).trigger('change');
                        }
                    })
                    .catch(error => console.error('Error fetching category icon:', error));
            }
        }
    });

    $('#createMapping').click(function() {
        const form = $('#createMappingForm')[0];
        const formData = new FormData(form);
        
        // Handle category_id specially for new categories
        const categorySelect = $('#category_id');
        const selectedOption = categorySelect.select2('data')[0];
        if (selectedOption && !selectedOption.id.match(/^\d+$/)) {
            formData.set('category_id', selectedOption.text);
        }
        
        // Add multiple roles
        const roles = $('#roles').val();
        if (roles) {
            formData.delete('roles');
            roles.forEach(role => formData.append('roles', role));
        }

        fetch('/admin/mapping', {
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
            alert('Error creating mapping');
        });
    });

    $('.edit-mapping').click(function() {
        const id = $(this).data('id');
        
        fetch(`/admin/mapping/${id}`)
        .then(response => response.json())
        .then(data => {
            $('#edit_mapping_id').val(id);
            $('#edit_page_name').val(data.page_name);
            $('#edit_route').val(data.route).trigger('change');
            $('#edit_category_id').val(data.category_id).trigger('change');
            $('#edit_icon').val(data.icon).trigger('change');
            $('#edit_roles').val(data.role_ids).trigger('change');
            
            if (data.category_icon) {
                $('#edit_category_icon').val(data.category_icon).trigger('change');
            }
            
            $('#editMappingModal').modal('show');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading mapping data');
        });
    });

    $('#updateMapping').click(function() {
        const id = $('#edit_mapping_id').val();
        const form = $('#editMappingForm')[0];
        const formData = new FormData(form);
        
        // Handle category_id specially for new categories
        const categorySelect = $('#edit_category_id');
        const selectedOption = categorySelect.select2('data')[0];
        if (selectedOption && !selectedOption.id.match(/^\d+$/)) {
            formData.set('category_id', selectedOption.text);
        }
        
        // Add multiple roles
        const roles = $('#edit_roles').val();
        if (roles) {
            formData.delete('roles');
            roles.forEach(role => formData.append('roles', role));
        }

        fetch(`/admin/mapping/${id}`, {
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
            alert('Error updating mapping');
        });
    });

    $('.delete-mapping').click(function() {
        const id = $(this).data('id');
        const name = $(this).data('name');
        
        $('#deleteConfirmText').text(`Mapping: ${name}`);
        $('#confirmDelete').data('id', id);
        $('#deleteConfirmModal').modal('show');
    });

    $('#confirmDelete').click(function() {
        const id = $(this).data('id');
        
        fetch(`/admin/mapping/${id}`, {
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
            alert('Error deleting mapping');
        });
    });

    // Hide category icon fields initially
    $('[name="category_icon"]').closest('.mb-3').hide();
});
