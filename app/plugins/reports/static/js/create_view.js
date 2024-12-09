$(document).ready(function() {
    // Set up CSRF token for AJAX requests
    var csrf_token = $('input[name=csrf_token]').val();
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

    // Initialize select2 for roles
    $('#roles').select2({
        placeholder: 'Select roles',
        allowClear: true
    });

    // Toggle roles selection based on private switch
    $('#isPrivate').change(function() {
        $('#rolesGroup').toggle(this.checked);
    });

    // Toggle transform configuration sections
    $('#transformType').change(function() {
        $('.transform-config').hide();
        const type = $(this).val();
        if (type) {
            $(`#${type}Config`).show();
            // Show/hide server-side option based on transform type
            $('#serverSide').closest('.form-check').toggle(
                ['python', 'regex'].includes(type)
            );
            if (['python', 'regex'].includes(type)) {
                $('#serverSide').prop('checked', true);
            }
        }
        updateTransformPreview();
    });

    // Toggle regex operation configs
    $('#regexOperation').change(function() {
        const op = $(this).val();
        $('#regexReplaceConfig').toggle(op === 'replace');
        $('#regexExtractConfig').toggle(op === 'extract');
        updateTransformPreview();
    });

    // Load database structure when database is selected
    $('#database').change(function() {
        const dbId = $(this).val();
        if (!dbId) {
            $('#dbStructure').html('<p class="text-muted">Select a database to view its structure</p>');
            return;
        }

        $.get(`/reports/api/database/${dbId}/tables`)
            .done(function(tables) {
                let html = '<div class="accordion" id="tablesAccordion">';
                Object.entries(tables).forEach(([tableName, columns], index) => {
                    html += `
                        <div class="card">
                            <div class="card-header" id="heading${index}">
                                <h2 class="mb-0">
                                    <button class="btn btn-link btn-block text-left" type="button" 
                                            data-toggle="collapse" data-target="#collapse${index}">
                                        ${tableName}
                                    </button>
                                </h2>
                            </div>
                            <div id="collapse${index}" class="collapse" 
                                 data-parent="#tablesAccordion">
                                <div class="card-body">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Column</th>
                                                <th>Type</th>
                                                <th>Nullable</th>
                                            </tr>
                                        </thead>
                                        <tbody>`;
                    
                    columns.forEach(column => {
                        html += `
                            <tr>
                                <td>${column.name}</td>
                                <td>${column.type}</td>
                                <td>${column.nullable ? 'Yes' : 'No'}</td>
                            </tr>`;
                    });
                    
                    html += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>`;
                });
                html += '</div>';
                $('#dbStructure').html(html);
            })
            .fail(function(xhr) {
                $('#dbStructure').html(`
                    <div class="alert alert-danger">
                        Error loading database structure: ${xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error'}
                    </div>
                `);
            });
    });

    // Test query
    $('#testQuery').click(function() {
        const data = {
            database_id: $('#database').val(),
            query: $('#query').val()
        };

        if (!data.database_id || !data.query) {
            alert('Please select a database and enter a query');
            return;
        }

        $.ajax({
            url: '/reports/api/test-query',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(result) {
                updateColumnList(result.columns, result.sample_data);
                updatePreviewTable([result.sample_data]);
            },
            error: function(xhr) {
                alert('Error testing query: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error'));
            }
        });
    });

    // Transform value function
    function transformValue(value, config) {
        if (!config || !config.type) return value;
        
        switch (config.type) {
            case 'url':
                const url = config.urlTemplate.replace('{value}', value);
                const text = config.urlText ? config.urlText.replace('{value}', value) : value;
                return `<a href="${url}" target="_blank">${text}</a>`;
                
            case 'date':
                if (!value) return '';
                const date = new Date(value);
                // Simple date formatting - could be enhanced with a date library
                const options = {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                };
                return date.toLocaleString(undefined, options);
                
            case 'number':
                if (value === null || value === undefined) return '';
                let num = parseFloat(value);
                if (isNaN(num)) return value;
                
                if (config.decimalPlaces !== undefined) {
                    num = num.toFixed(config.decimalPlaces);
                }
                
                if (config.useThousandsSeparator) {
                    num = num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                }
                
                return (config.prefix || '') + num + (config.suffix || '');
                
            case 'boolean':
                return value ? (config.trueDisplay || 'Yes') : (config.falseDisplay || 'No');
                
            case 'custom':
                try {
                    const transform = new Function('value', config.code);
                    return transform(value);
                } catch (e) {
                    console.error('Error in custom transform:', e);
                    return value;
                }
                
            default:
                return value;
        }
    }

    // Get transform configuration
    function getTransformConfig() {
        const type = $('#transformType').val();
        let config = { 
            type,
            server_side: $('#serverSide').is(':checked')
        };

        if (type) {
            switch (type) {
                case 'url':
                    config.urlTemplate = $('#urlTemplate').val();
                    config.urlText = $('#urlText').val();
                    break;
                case 'date':
                    config.format = $('#dateFormat').val();
                    break;
                case 'number':
                    config.decimalPlaces = $('#decimalPlaces').val();
                    config.useThousandsSeparator = $('#useThousandsSeparator').is(':checked');
                    config.prefix = $('#numberPrefix').val();
                    config.suffix = $('#numberSuffix').val();
                    break;
                case 'boolean':
                    config.trueDisplay = $('#trueDisplay').val();
                    config.falseDisplay = $('#falseDisplay').val();
                    break;
                case 'python':
                    config.code = $('#pythonExpression').val();
                    break;
                case 'regex':
                    config.pattern = $('#regexPattern').val();
                    const operation = $('#regexOperation').val();
                    if (operation === 'match') {
                        config.match_only = true;
                    } else if (operation === 'extract') {
                        config.extract_group = parseInt($('#regexGroup').val());
                    } else {
                        config.replacement = $('#regexReplacement').val();
                    }
                    config.case_insensitive = $('#regexCaseInsensitive').is(':checked');
                    config.multiline = $('#regexMultiline').is(':checked');
                    break;
                case 'custom':
                    config.code = $('#customTransform').val();
                    break;
            }
        }
        return config;
    }

    // Load transform configuration
    function loadTransformConfig(config) {
        $('#transformType').val(config.type).trigger('change');
        $('#serverSide').prop('checked', config.server_side || false);
        
        switch (config.type) {
            case 'url':
                $('#urlTemplate').val(config.urlTemplate);
                $('#urlText').val(config.urlText);
                break;
            case 'date':
                $('#dateFormat').val(config.format);
                break;
            case 'number':
                $('#decimalPlaces').val(config.decimalPlaces);
                $('#useThousandsSeparator').prop('checked', config.useThousandsSeparator);
                $('#numberPrefix').val(config.prefix);
                $('#numberSuffix').val(config.suffix);
                break;
            case 'boolean':
                $('#trueDisplay').val(config.trueDisplay);
                $('#falseDisplay').val(config.falseDisplay);
                break;
            case 'python':
                $('#pythonExpression').val(config.code);
                break;
            case 'regex':
                $('#regexPattern').val(config.pattern);
                $('#regexOperation').val(config.match_only ? 'match' : 
                                       config.extract_group !== undefined ? 'extract' : 'replace')
                                  .trigger('change');
                $('#regexReplacement').val(config.replacement);
                $('#regexGroup').val(config.extract_group || 0);
                $('#regexCaseInsensitive').prop('checked', config.case_insensitive);
                $('#regexMultiline').prop('checked', config.multiline);
                break;
            case 'custom':
                $('#customTransform').val(config.code);
                break;
        }
    }

    // Reset transform configuration
    function resetTransformConfig() {
        $('#transformType').val('').trigger('change');
        $('#serverSide').prop('checked', false);
        $('.transform-input').val('');
        $('input[type="checkbox"].transform-input').prop('checked', false);
    }

    // Update column list to use table rows
    function updateColumnList(columns, sampleData) {
        let html = '';
        columns.forEach((column, index) => {
            html += `
                <tr>
                    <td>${column}</td>
                    <td>
                        <input type="text" class="form-control form-control-sm" 
                               name="headers[${index}]" 
                               value="${column}">
                    </td>
                    <td>
                        <div class="custom-control custom-switch">
                            <input type="checkbox" class="custom-control-input" 
                                   name="visible[${index}]" checked>
                        </div>
                    </td>
                    <td>
                        <div class="custom-control custom-switch">
                            <input type="checkbox" class="custom-control-input" 
                                   name="sortable[${index}]" checked>
                        </div>
                    </td>
                    <td>
                        <div class="custom-control custom-switch">
                            <input type="checkbox" class="custom-control-input" 
                                   name="searchable[${index}]" checked>
                        </div>
                    </td>
                    <td>
                        <button type="button" class="btn btn-sm btn-info configure-transform"
                                data-column-index="${index}" data-column-name="${column}">
                            <i class="fas fa-magic"></i>
                        </button>
                        <input type="hidden" name="transform[${index}]" value="">
                    </td>
                    <td class="preview-cell">
                        ${sampleData[column]}
                    </td>
                </tr>
            `;
        });
        $('#columnList').html(html);

        // Initialize transform configuration
        $('.configure-transform').click(function() {
            const columnIndex = $(this).data('column-index');
            const columnName = $(this).data('column-name');
            $('#transformColumnIndex').val(columnIndex);
            $('#transformColumnName').text(columnName);
            $('#transformPreviewInput').val(sampleData[columnName]);
            
            const transform = $(`input[name="transform[${columnIndex}]"]`).val();
            if (transform) {
                loadTransformConfig(JSON.parse(transform));
            } else {
                resetTransformConfig();
            }
            
            updateTransformPreview();
            $('#transformModal').modal('show');
        });
    }

    // Save transform configuration
    $('#saveTransform').click(function() {
        const columnIndex = $('#transformColumnIndex').val();
        const config = getTransformConfig();
        $(`input[name="transform[${columnIndex}]"]`).val(JSON.stringify(config));
        
        // Update preview cell
        const value = $('#transformPreviewInput').val();
        const preview = config.type && !config.server_side ? transformValue(value, config) : value;
        $(`#columnList tr:eq(${columnIndex}) .preview-cell`).html(preview);
        
        $('#transformModal').modal('hide');
    });

    // Live preview for transforms
    $('.transform-input').on('input change', function() {
        updateTransformPreview();
    });

    function updateTransformPreview() {
        const value = $('#transformPreviewInput').val();
        const type = $('#transformType').val();
        let preview = value;

        try {
            if (type) {
                const config = getTransformConfig();
                if (config.server_side) {
                    preview = '<em>Server-side transform - preview not available</em>';
                } else {
                    preview = transformValue(value, config);
                }
            }
            $('#transformPreviewOutput').html(preview);
        } catch (e) {
            $('#transformPreviewOutput').html(`<span class="text-danger">Error: ${e.message}</span>`);
        }
    }

    // Update preview table
    function updatePreviewTable(data) {
        const columns = $('#columnList tr').map(function() {
            const index = $(this).find('.configure-transform').data('column-index');
            return {
                name: $(this).find(`input[name="headers[${index}]"]`).val(),
                original: $(this).find('td:first').text(),
                visible: $(this).find(`input[name="visible[${index}]"]`).is(':checked'),
                transform: $(this).find(`input[name="transform[${index}]"]`).val()
            };
        }).get();

        // Update headers
        let headerHtml = '<tr>';
        columns.forEach(col => {
            if (col.visible) {
                headerHtml += `<th>${col.name}</th>`;
            }
        });
        headerHtml += '</tr>';
        $('#previewHeaders').html(headerHtml);

        // Update data
        let dataHtml = '';
        data.forEach(row => {
            dataHtml += '<tr>';
            columns.forEach(col => {
                if (col.visible) {
                    let value = row[col.original];
                    if (col.transform) {
                        const config = JSON.parse(col.transform);
                        if (!config.server_side) {
                            value = transformValue(value, config);
                        }
                    }
                    dataHtml += `<td>${value}</td>`;
                }
            });
            dataHtml += '</tr>';
        });
        $('#previewData').html(dataHtml);
    }

    // Form submission
    $('#createViewForm').submit(function(e) {
        e.preventDefault();

        // Gather column configuration
        const columnConfig = [];
        $('#columnList tr').each(function(index) {
            const transform = $(`input[name="transform[${index}]"]`).val();
            columnConfig.push({
                original: $(this).find('td:first').text(),
                display: $(this).find(`input[name="headers[${index}]"]`).val(),
                visible: $(this).find(`input[name="visible[${index}]"]`).is(':checked'),
                sortable: $(this).find(`input[name="sortable[${index}]"]`).is(':checked'),
                searchable: $(this).find(`input[name="searchable[${index}]"]`).is(':checked'),
                transform: transform ? JSON.parse(transform) : null
            });
        });

        const data = {
            title: $('#title').val(),
            description: $('#description').val(),
            database_id: $('#database').val(),
            query: $('#query').val(),
            column_config: columnConfig,
            is_private: $('#isPrivate').is(':checked'),
            roles: $('#isPrivate').is(':checked') ? $('#roles').val() : []
        };

        $.ajax({
            url: '/reports/view/new',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                window.location.href = '/reports/';
            },
            error: function(xhr) {
                alert('Error creating view: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error'));
            }
        });
    });
});
