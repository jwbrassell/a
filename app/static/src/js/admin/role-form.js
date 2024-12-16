$(document).ready(function() {
    // Initialize Bootstrap tabs
    $('.nav-tabs a').on('click', function(e) {
        e.preventDefault();
        $(this).tab('show');
    });

    // Initialize Select2 for LDAP groups
    $('#ldap_groups').select2({
        placeholder: 'Select LDAP groups...',
        allowClear: true,
        tags: true,
        width: '100%'
    });

    // Form validation
    $('#role-form').submit(function(e) {
        const name = $('#name').val().trim();
        const description = $('#description').val().trim();
        
        if (!name || !description) {
            e.preventDefault();
            Swal.fire({
                title: 'Error',
                text: 'Role name and description are required',
                icon: 'error'
            });
        }
    });

    // Delete role confirmation
    $('#delete-role').click(function(e) {
        e.preventDefault();
        Swal.fire({
            title: 'Delete Role?',
            text: 'This action cannot be undone!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            confirmButtonText: 'Yes, delete it!'
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = $(this).data('delete-url');
            }
        });
    });

    // Auto-save functionality
    let autoSaveTimeout;
    const autoSaveDelay = 1000; // 1 second

    function scheduleAutoSave() {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(function() {
            const formData = $('#role-form').serialize();
            $.ajax({
                url: $('#role-form').attr('action'),
                method: 'POST',
                data: formData,
                success: function(response) {
                    toastr.success('Changes saved automatically');
                },
                error: function(xhr) {
                    toastr.error('Error saving changes');
                }
            });
        }, autoSaveDelay);
    }

    // Watch for changes in form inputs
    $('#role-form :input').on('change input', function() {
        scheduleAutoSave();
    });

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Handle tab state persistence
    const activeTab = sessionStorage.getItem('roleFormActiveTab');
    if (activeTab) {
        $('.nav-tabs a[href="' + activeTab + '"]').tab('show');
    }

    // Save active tab state
    $('.nav-tabs a').on('shown.bs.tab', function(e) {
        sessionStorage.setItem('roleFormActiveTab', $(e.target).attr('href'));
    });
});
