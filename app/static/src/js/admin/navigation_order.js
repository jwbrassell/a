document.addEventListener('DOMContentLoaded', function() {
    let hasChanges = false;
    const saveButton = document.querySelector('.floating-save');
    
    // Initialize main Sortable for categories and standalone items
    const mainSortable = new Sortable(document.getElementById('sortable-nav'), {
        animation: 150,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        dragClass: 'dragging',
        draggable: '.category-group, .sortable-item:not(.category-item):not(.category)',
        group: {
            name: 'main',
            put: function(to, from, dragged) {
                // Allow items to be dropped in main list (making them standalone)
                if (dragged.classList.contains('category-item')) {
                    dragged.classList.remove('category-item');
                    delete dragged.dataset.category;
                    return true;
                }
                // Don't allow categories to be dropped as standalone items
                return !dragged.classList.contains('category');
            }
        },
        onStart: function(evt) {
            if (evt.item.classList.contains('category-group')) {
                evt.item.classList.add('dragging');
            } else {
                document.querySelectorAll('.category-group').forEach(group => {
                    group.classList.add('drop-target');
                });
            }
        },
        onEnd: function(evt) {
            evt.item.classList.remove('dragging');
            document.querySelectorAll('.category-group').forEach(group => {
                group.classList.remove('drop-target');
            });
            hasChanges = true;
            saveButton.classList.add('show');
        }
    });

    // Initialize Sortable for items within each category
    document.querySelectorAll('.category-group').forEach(group => {
        new Sortable(group, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            dragClass: 'dragging',
            draggable: '.category-item',
            group: {
                name: 'links',
                pull: true,
                put: function(to, from, dragged) {
                    // Don't allow categories to be dropped into other categories
                    if (dragged.classList.contains('category') || 
                        dragged.classList.contains('category-group')) {
                        return false;
                    }
                    
                    // Allow links to be dropped into categories
                    dragged.classList.add('category-item');
                    dragged.dataset.category = group.dataset.category;
                    return true;
                }
            },
            onStart: function(evt) {
                evt.item.classList.add('dragging');
                // Show visual indicator that items can be dragged to main list
                document.getElementById('sortable-nav').classList.add('drop-target');
            },
            onEnd: function(evt) {
                evt.item.classList.remove('dragging');
                document.getElementById('sortable-nav').classList.remove('drop-target');
                hasChanges = true;
                saveButton.classList.add('show');
            }
        });
    });

    // Save button click handler
    document.getElementById('save-order').addEventListener('click', function() {
        saveChanges();
    });

    function saveChanges() {
        const form = document.getElementById('nav-order-form');
        const orderData = [];
        let weight = 0;

        // Process all items in order, including categories and their items
        document.querySelectorAll('#sortable-nav > .category-group, #sortable-nav > .sortable-item:not(.category-item)').forEach(item => {
            if (item.classList.contains('category-group')) {
                // Process items within the category
                item.querySelectorAll('.category-item').forEach(categoryItem => {
                    orderData.push({
                        id: categoryItem.dataset.id,
                        weight: weight++,
                        category: item.dataset.category
                    });
                });
            } else if (item.dataset.type === 'link') {
                // Process standalone items
                orderData.push({
                    id: item.dataset.id,
                    weight: weight++,
                    category: null
                });
            }
        });

        // Send the order data to the server
        fetch('/admin/update_nav_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': form.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({ order: orderData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reset changes flag and hide save button
                hasChanges = false;
                saveButton.classList.remove('show');
                
                // Show success toast
                const Toast = Swal.mixin({
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 1500,
                    timerProgressBar: true,
                    didOpen: (toast) => {
                        toast.addEventListener('mouseenter', Swal.stopTimer)
                        toast.addEventListener('mouseleave', Swal.resumeTimer)
                    }
                });

                Toast.fire({
                    icon: 'success',
                    title: 'Changes saved'
                }).then(() => {
                    window.location.reload();
                });
            } else {
                throw new Error(data.message || 'Error saving changes');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
            });

            Toast.fire({
                icon: 'error',
                title: 'Error saving changes'
            });
        });
    }

    // Warn about unsaved changes
    window.addEventListener('beforeunload', function(e) {
        if (hasChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
});
