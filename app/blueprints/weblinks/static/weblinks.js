// Icon Search and Loading
function initializeIconSearch() {
    $('#linkIcon').select2({
        theme: 'bootstrap4',
        templateResult: formatIconOption,
        templateSelection: formatIconOption,
        dropdownParent: $('#linkModal'),
        ajax: {
            url: '/weblinks/search_icons',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term || '',
                    page: params.page || 1
                };
            },
            processResults: function(data, params) {
                params.page = params.page || 1;
                return {
                    results: data.icons.map(icon => ({
                        id: icon,
                        text: icon
                    })),
                    pagination: {
                        more: data.has_more
                    }
                };
            },
            cache: true
        },
        minimumInputLength: 0,
        placeholder: 'Search icons...'
    }).on('select2:select', function(e) {
        // Update icon preview when selection changes
        $('#iconPreview').attr('class', e.params.data.id);
    });
}

function formatIconOption(icon) {
    if (!icon.id) return icon.text;
    return $(`<span><i class="${icon.id} icon-preview"></i> ${icon.text}</span>`);
}

// Tag Management
function initializeTagSelect() {
    $('#linkTags').select2({
        theme: 'bootstrap4',
        tags: true,
        tokenSeparators: [',', ' '],
        placeholder: 'Select or add tags',
        dropdownParent: $('#linkModal'),
        templateSelection: function(data) {
            if (!data.id) return data.text;
            return $(`<span class="badge bg-info">${data.text}</span>`);
        }
    });
}

// DataTable Initialization
function initializeDataTable() {
    const table = $('#linksTable').DataTable({
        ajax: {
            url: "/weblinks/get_links",
            dataSrc: ''
        },
        columns: [
            { 
                data: 'icon',
                width: '50px',
                render: function(data) {
                    return `<i class="${data || 'fas fa-link'} fa-lg"></i>`;
                }
            },
            { 
                data: 'title',
                width: '15%'
            },
            { 
                data: 'url',
                width: '40%',
                render: function(data) {
                    return `<a href="${data}" target="_blank">${data}</a>`;
                }
            },
            { 
                data: 'tags',
                width: '20%',
                render: function(data) {
                    return data.map(tag => 
                        `<span class="badge bg-info">${tag}</span>`
                    ).join(' ');
                }
            },
            { 
                data: 'created_by',
                width: '10%'
            },
            {
                data: null,
                width: '100px',
                render: function(data, type, row) {
                    let buttons = `<button class="btn btn-sm btn-info" onclick="viewLink(${row.id})">
                        <i class="fas fa-eye"></i>
                    </button>`;
                    if (hasPermission()) {
                        buttons += `
                            <button class="btn btn-sm btn-primary ms-1" onclick="editLink(${row.id})">
                                <i class="fas fa-edit"></i>
                            </button>`;
                    }
                    return buttons;
                }
            }
        ],
        dom: 'Bfrtip',
        buttons: ['copy', 'csv', 'excel'],
        order: [[1, 'asc']],
        autoWidth: false,
        scrollX: true,
        scrollCollapse: true,
        fixedColumns: true,
        responsive: true
    });

    // Add resize handler
    let resizeTimeout;
    $(window).on('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            table.columns.adjust().draw();
        }, 150);
    });

    // Initial column adjustment
    table.columns.adjust().draw();

    return table;
}

// Modal Management
let linkModal = null;
let viewLinkModal = null;

function initializeModals() {
    linkModal = new bootstrap.Modal(document.getElementById('linkModal'));
    viewLinkModal = new bootstrap.Modal(document.getElementById('viewLinkModal'));
}

// Edit Link
function editLink(id) {
    currentLinkId = id;
    $('#linkModalTitle').text('Edit Link');
    
    $.get(`/weblinks/get_link/${id}`, function(link) {
        $('#linkTitle').val(link.title);
        $('#linkUrl').val(link.url);
        $('#linkDescription').val(link.description);
        
        // Set icon with proper data structure for Select2
        const iconOption = new Option(link.icon, link.icon, true, true);
        $('#linkIcon')
            .empty()
            .append(iconOption)
            .trigger('change');
        $('#iconPreview').attr('class', link.icon);
        
        // Set tags with proper data structure for Select2
        const tagOptions = link.tags.map(tag => new Option(tag, tag, true, true));
        $('#linkTags')
            .empty()
            .append(tagOptions)
            .trigger('change');
        
        linkModal.show();
    });
}

// View Link
function viewLink(id) {
    $.get(`/weblinks/get_link/${id}`, function(link) {
        const details = $('#linkDetails');
        details.html(`
            <div class="mb-3">
                <h6>Title</h6>
                <p>${link.title}</p>
            </div>
            <div class="mb-3">
                <h6>URL</h6>
                <p><a href="${link.url}" target="_blank">${link.url}</a></p>
            </div>
            <div class="mb-3">
                <h6>Description</h6>
                <p>${link.description || 'No description'}</p>
            </div>
            <div class="mb-3">
                <h6>Icon</h6>
                <p><i class="${link.icon}"></i> ${link.icon}</p>
            </div>
            <div class="mb-3">
                <h6>Tags</h6>
                <p>${link.tags.map(tag => 
                    `<span class="badge bg-info">${tag}</span>`
                ).join(' ') || 'No tags'}</p>
            </div>
        `);

        const history = $('#linkHistory');
        history.empty();
        link.history.forEach(entry => {
            const changes = formatChanges(entry.changes);
            if (changes.length > 0) {
                history.append(`
                    <div class="history-item">
                        <div class="history-meta">
                            <i class="fas fa-user"></i> ${entry.changed_by}
                            <span class="history-date">
                                <i class="fas fa-clock"></i> ${new Date(entry.changed_at).toLocaleString()}
                            </span>
                        </div>
                        <div class="history-changes">
                            ${changes.map(change => `<div class="history-change">${change}</div>`).join('')}
                        </div>
                    </div>
                `);
            }
        });

        viewLinkModal.show();
    });
}

// Format Changes for History
function formatChanges(changes) {
    let formattedChanges = [];
    
    // Handle icon changes specially since they're nested
    if (changes.icon) {
        const iconChange = changes.icon;
        if (iconChange.new && iconChange.old) {
            formattedChanges.push(`Icon changed from "${iconChange.old}" to "${iconChange.new}"`);
        } else if (iconChange.new) {
            formattedChanges.push(`Icon set to "${iconChange.new}"`);
        }
    }
    
    // Handle other direct changes
    for (const [key, value] of Object.entries(changes)) {
        if (key === 'icon') continue; // Skip icon as it's already handled
        
        if (typeof value === 'object' && value !== null) {
            if (value.new && value.old) {
                // Format arrays nicely
                if (Array.isArray(value.new) && Array.isArray(value.old)) {
                    formattedChanges.push(`${key.charAt(0).toUpperCase() + key.slice(1)} changed from [${value.old.join(', ')}] to [${value.new.join(', ')}]`);
                } else {
                    formattedChanges.push(`${key.charAt(0).toUpperCase() + key.slice(1)} changed from "${value.old}" to "${value.new}"`);
                }
            } else if (value.new) {
                if (Array.isArray(value.new)) {
                    formattedChanges.push(`${key.charAt(0).toUpperCase() + key.slice(1)} set to [${value.new.join(', ')}]`);
                } else {
                    formattedChanges.push(`${key.charAt(0).toUpperCase() + key.slice(1)} set to "${value.new}"`);
                }
            }
        }
    }
    
    return formattedChanges;
}

// Initialize everything when document is ready
$(document).ready(function() {
    initializeModals();
    initializeIconSearch();
    initializeTagSelect();
    window.linksTable = initializeDataTable();
    loadCommonLinks();
});

// Common Links
function loadCommonLinks() {
    $.get("/weblinks/get_common_links", function(links) {
        const container = $('#commonLinks');
        container.empty();
        links.forEach(link => {
            container.append(`
                <a href="${link.url}" target="_blank" class="common-link-card" 
                   onclick="recordClick(${link.id})" title="${link.title}">
                    <div class="common-link-icon-wrapper">
                        <i class="${link.icon || 'fas fa-link'} common-link-icon"></i>
                    </div>
                    <div class="common-link-title">${link.title}</div>
                </a>
            `);
        });
    });
}

function recordClick(id) {
    $.post(`/weblinks/record_click/${id}`);
}

function showAddLinkModal() {
    currentLinkId = null;
    $('#linkModalTitle').text('Add Link');
    $('#linkForm')[0].reset();
    $('#linkTags').val(null).trigger('change');
    $('#linkIcon').val('fas fa-link').trigger('change');
    linkModal.show();
}

function hasPermission() {
    return $('#linksTable').data('canEdit');
}
