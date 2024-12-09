// Transform value function
function transformValue(value, config) {
    if (!config || !config.type) return value;
    
    switch (config.type) {
        case 'url':
            var url = config.urlTemplate.replace('{value}', value);
            var text = config.urlText ? config.urlText.replace('{value}', value) : value;
            return '<a href="' + url + '" target="_blank">' + text + '</a>';
            
        case 'date':
            if (!value) return '';
            var date = new Date(value);
            var options = {
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
            var num = parseFloat(value);
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
                var transform = new Function('value', config.code);
                return transform(value);
            } catch (e) {
                console.error('Error in custom transform:', e);
                return value;
            }
            
        default:
            return value;
    }
}

// Update column list to use table rows
function updateColumnList(columns, sampleData) {
    var html = '';
    columns.forEach(function(column, index) {
        html += '<tr>' +
            '<td>' + column + '</td>' +
            '<td>' +
                '<input type="text" class="form-control form-control-sm" ' +
                       'name="headers[' + index + ']" ' +
                       'value="' + column + '">' +
            '</td>' +
            '<td>' +
                '<div class="custom-control custom-switch">' +
                    '<input type="checkbox" class="custom-control-input" ' +
                           'id="visible' + index + '" ' +
                           'name="visible[' + index + ']" checked>' +
                    '<label class="custom-control-label" for="visible' + index + '"></label>' +
                '</div>' +
            '</td>' +
            '<td>' +
                '<div class="custom-control custom-switch">' +
                    '<input type="checkbox" class="custom-control-input" ' +
                           'id="sortable' + index + '" ' +
                           'name="sortable[' + index + ']" checked>' +
                    '<label class="custom-control-label" for="sortable' + index + '"></label>' +
                '</div>' +
            '</td>' +
            '<td>' +
                '<div class="custom-control custom-switch">' +
                    '<input type="checkbox" class="custom-control-input" ' +
                           'id="searchable' + index + '" ' +
                           'name="searchable[' + index + ']" checked>' +
                    '<label class="custom-control-label" for="searchable' + index + '"></label>' +
                '</div>' +
            '</td>' +
            '<td>' +
                '<button type="button" class="btn btn-sm btn-info configure-transform" ' +
                        'data-column-index="' + index + '" data-column-name="' + column + '">' +
                    '<i class="fas fa-magic"></i>' +
                '</button>' +
                '<input type="hidden" name="transform[' + index + ']" value="">' +
            '</td>' +
            '<td class="preview-cell">' +
                (sampleData[column] !== undefined ? sampleData[column] : '') +
            '</td>' +
        '</tr>';
    });
    $('#columnList').html(html);

    // Initialize transform configuration
    $('.configure-transform').click(function() {
        var columnIndex = $(this).data('column-index');
        var columnName = $(this).data('column-name');
        $('#transformColumnIndex').val(columnIndex);
        $('#transformColumnName').text(columnName);
        $('#transformPreviewInput').val(sampleData[columnName]);
        
        var transform = $('input[name="transform[' + columnIndex + ']"]').val();
        if (transform) {
            loadTransformConfig(JSON.parse(transform));
        } else {
            resetTransformConfig();
        }
        
        updateTransformPreview();
        $('#transformModal').modal('show');
    });
}

// Update preview table
function updatePreviewTable(data) {
    var columns = $('#columnList tr').map(function() {
        var index = $(this).find('.configure-transform').data('column-index');
        return {
            name: $('input[name="headers[' + index + ']"]').val(),
            original: $(this).find('td:first').text(),
            visible: $('input[name="visible[' + index + ']"]').is(':checked'),
            transform: $('input[name="transform[' + index + ']"]').val()
        };
    }).get();

    // Update headers
    var headerHtml = '<tr>';
    columns.forEach(function(col) {
        if (col.visible) {
            headerHtml += '<th>' + col.name + '</th>';
        }
    });
    headerHtml += '</tr>';
    $('#previewHeaders').html(headerHtml);

    // Update data
    var dataHtml = '';
    data.forEach(function(row) {
        dataHtml += '<tr>';
        columns.forEach(function(col) {
            if (col.visible) {
                var value = row[col.original];
                if (col.transform) {
                    var config = JSON.parse(col.transform);
                    if (!config.server_side) {
                        value = transformValue(value, config);
                    }
                }
                dataHtml += '<td>' + (value !== null ? value : '') + '</td>';
            }
        });
        dataHtml += '</tr>';
    });
    $('#previewData').html(dataHtml);
}
