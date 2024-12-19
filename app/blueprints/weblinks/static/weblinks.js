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

// Create Link Card
function createLinkCard(link) {
    return `
        <div class="col d-flex justify-content-center align-items-center">
            <a href="${link.url}" target="_blank" class="info-box" onclick="recordClick(${link.id})" title="${link.title}">
                <div class="info-box-content">
                    <div class="info-box-icon bg-info elevation-1">
                        <i class="${link.icon || 'fas fa-link'}"></i>
                    </div>
                    <span class="info-box-text">${link.title}</span>
                    ${(link.tags || []).length > 0 ? `
                        <div class="info-box-tags">
                            ${link.tags.map(tag => `<span class="badge bg-secondary">${tag}</span>`).join(' ')}
                        </div>
                    ` : ''}
                </div>
            </a>
        </div>
    `;
}

// DataTable Initialization
function initializeDataTable() {
    return $('#linksTable').DataTable({
        ajax: {
            url: "/weblinks/get_links",
            dataSrc: ''
        },
        columns: [
            { 
                data: 'icon',
                render: function(data) {
                    return `<i class="${data || 'fas fa-link'} fa-lg"></i>`;
                }
            },
            { data: 'title' },
            { 
                data: 'url',
                render: function(data) {
                    return `<a href="${data}" target="_blank">${data}</a>`;
                }
            },
            { 
                data: 'tags',
                render: function(data) {
                    return (data || []).map(tag => 
                        `<span class="badge bg-info">${tag}</span>`
                    ).join(' ');
                }
            },
            { data: 'created_by' },
            {
                data: null,
                render: function(data, type, row) {
                    let buttons = `<button class="btn btn-sm btn-info" onclick="viewLink(${row.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>`;
                    if (hasPermission()) {
                        buttons += `
                            <button class="btn btn-sm btn-primary ms-1" onclick="editLink(${row.id})" title="Edit Link">
                                <i class="fas fa-edit"></i>
                            </button>`;
                    }
                    return buttons;
                }
            }
        ]
    });
}

// Common Links
function loadCommonLinks() {
    $.get("/weblinks/get_common_links", function(links) {
        const container = $('#commonLinks');
        container.empty();
        links.forEach(link => {
            container.append(createLinkCard(link));
        });
    });
}

// Modal Management
let currentLinkId = null;
let lastFocusedElement = null;

function initializeModals() {
    const linkModalEl = document.getElementById('linkModal');
    const viewLinkModalEl = document.getElementById('viewLinkModal');

    // Initialize modals with proper focus management
    const linkModal = new bootstrap.Modal(linkModalEl, {
        backdrop: 'static',
        keyboard: true
    });

    const viewLinkModal = new bootstrap.Modal(viewLinkModalEl, {
        backdrop: 'static',
        keyboard: true
    });

    // Store last focused element before modal opens
    linkModalEl.addEventListener('show.bs.modal', function () {
        lastFocusedElement = document.activeElement;
    });

    viewLinkModalEl.addEventListener('show.bs.modal', function () {
        lastFocusedElement = document.activeElement;
    });

    // Return focus to the last focused element when modal closes
    linkModalEl.addEventListener('hidden.bs.modal', function () {
        if (lastFocusedElement) {
            lastFocusedElement.focus();
        }
    });

    viewLinkModalEl.addEventListener('hidden.bs.modal', function () {
        if (lastFocusedElement) {
            lastFocusedElement.focus();
        }
    });

    // Store modal instances
    window.linkModal = linkModal;
    window.viewLinkModal = viewLinkModal;
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
        const tagOptions = (link.tags || []).map(tag => new Option(tag, tag, true, true));
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
                <p>${(link.tags || []).map(tag => 
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

function saveLink() {
    const data = {
        title: $('#linkTitle').val(),
        url: $('#linkUrl').val(),
        description: $('#linkDescription').val(),
        icon: $('#linkIcon').val(),
        tags: $('#linkTags').val() || []
    };

    const url = currentLinkId ? 
        `/weblinks/update_link/${currentLinkId}` :
        "/weblinks/create_link";
    
    $.ajax({
        url: url,
        method: currentLinkId ? 'PUT' : 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function() {
            linkModal.hide();
            if (window.linksTable) {
                window.linksTable.ajax.reload();
            }
            loadCommonLinks();
        },
        error: function(xhr) {
            alert(xhr.responseJSON?.error || 'Error saving link');
        }
    });
}

function hasPermission() {
    return $('#linksTable').data('canEdit');
}

// Initialize everything when document is ready
$(document).ready(function() {
    initializeModals();
    initializeIconSearch();
    initializeTagSelect();
    window.linksTable = initializeDataTable();
    loadCommonLinks();
});
