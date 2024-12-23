document.addEventListener('DOMContentLoaded', function() {
    var currentDate = new Date();
    var currentMonth = currentDate.getMonth();
    var currentYear = currentDate.getFullYear();
    var selectedTeam = '';
    
    // API endpoints
    var urls = {
        events: "/oncall/api/events",
        current: "/oncall/api/current",
        upload: "/oncall/api/upload",
        teams: "/oncall/api/teams",
        holidays: "/oncall/api/holidays",
        uploadHolidays: "/oncall/api/holidays/upload"
    };
    
    // Team filter handler
    document.getElementById('team-filter').onchange = function() {
        selectedTeam = this.value;
        updateCalendar();
        loadCurrentOnCall();
    };

    // Handle template downloads without showing loader
    document.querySelectorAll('a[href*="template.csv"]').forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't show loader for template downloads
            e.stopPropagation();
            return true;
        });
    });

    // Auto-generate checkbox handler
    if (document.getElementById('auto_generate')) {
        document.getElementById('auto_generate').onchange = function() {
            var helpText = document.getElementById('csv-help-text');
            var manualTemplate = document.getElementById('manual-template');
            var autoTemplate = document.getElementById('auto-template');
            
            if (this.checked) {
                helpText.textContent = 'Required columns: name, phone';
                manualTemplate.style.display = 'none';
                autoTemplate.style.display = 'block';
            } else {
                helpText.textContent = 'Required columns: week, name, phone';
                manualTemplate.style.display = 'block';
                autoTemplate.style.display = 'none';
            }
        };
    }
    
    function updateCalendar() {
        var startDate = new Date(currentYear, currentMonth, 1);
        var endDate = new Date(currentYear, currentMonth + 1, 0);
        
        var params = {
            start: startDate.toISOString(),
            end: endDate.toISOString()
        };
        
        if (selectedTeam) {
            params.team = selectedTeam;
        }

        console.log('Fetching events for:', params);
        
        window.showAjaxLoader();
        fetch(urls.events + "?" + new URLSearchParams(params))
            .then(response => response.json())
            .then(events => {
                console.log('Received events:', events);
                
                // Update month/year display
                document.getElementById('current-month').textContent = 
                    startDate.toLocaleString('default', { month: 'long', year: 'numeric' });
                
                // Clear existing calendar
                var calendarBody = document.getElementById('calendar-body');
                calendarBody.innerHTML = '';
                
                // Calculate first day of month (0 = Sunday)
                var firstDay = startDate.getDay();
                var totalDays = endDate.getDate();
                var date = 1;
                var rows = Math.ceil((firstDay + totalDays) / 7);
                
                // Build calendar
                for (var i = 0; i < rows; i++) {
                    var row = document.createElement('tr');
                    
                    for (var j = 0; j < 7; j++) {
                        var cell = document.createElement('td');
                        cell.className = 'calendar-day';
                        
                        if (i === 0 && j < firstDay) {
                            // Empty cells before first day
                            cell.className += ' disabled';
                        } else if (date > totalDays) {
                            // Empty cells after last day
                            cell.className += ' disabled';
                        } else {
                            // Regular day cell
                            var currentDate = new Date(currentYear, currentMonth, date);
                            var dateDiv = document.createElement('div');
                            dateDiv.className = 'date';
                            dateDiv.textContent = date;
                            cell.appendChild(dateDiv);
                            
                            // Check for events on this day
                            var dayEvents = events.filter(event => {
                                var eventStart = new Date(event.start);
                                var eventEnd = new Date(event.end);
                                var cellDate = new Date(currentYear, currentMonth, date);
                                return cellDate >= eventStart && cellDate < eventEnd;
                            });
                            
                            // Add events to cell
                            dayEvents.forEach(event => {
                                if (event.display === 'background') {
                                    cell.style.backgroundColor = event.backgroundColor;
                                    cell.style.position = 'relative';
                                    var holidayDiv = document.createElement('div');
                                    holidayDiv.className = 'holiday-label';
                                    holidayDiv.textContent = event.title;
                                    cell.appendChild(holidayDiv);
                                } else {
                                    var eventDiv = document.createElement('div');
                                    eventDiv.className = `event ${event.classNames.join(' ')}`;
                                    eventDiv.innerHTML = `
                                        <strong>${event.title}</strong><br>
                                        <small>${event.description || ''}</small>
                                    `;
                                    cell.appendChild(eventDiv);
                                }
                            });
                            
                            // Highlight current day
                            if (date === new Date().getDate() &&
                                currentMonth === new Date().getMonth() &&
                                currentYear === new Date().getFullYear()) {
                                cell.className += ' today';
                            }
                            
                            date++;
                        }
                        
                        row.appendChild(cell);
                    }
                    
                    calendarBody.appendChild(row);
                }
            })
            .catch(error => {
                console.error('Error updating calendar:', error);
                toastr.error('Error loading calendar events');
            })
            .finally(() => {
                window.hideAjaxLoader();
            });
    }
    
    // Navigation handlers
    document.getElementById('prev-month').onclick = function() {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        updateCalendar();
    };
    
    document.getElementById('next-month').onclick = function() {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        updateCalendar();
    };
    
    document.getElementById('today').onclick = function() {
        currentMonth = new Date().getMonth();
        currentYear = new Date().getFullYear();
        updateCalendar();
    };
    
    // Current on-call information
    function loadCurrentOnCall() {
        var params = {};
        if (selectedTeam) {
            params.team = selectedTeam;
        }
        
        window.showAjaxLoader();
        fetch(urls.current + "?" + new URLSearchParams(params))
            .then(response => response.json())
            .then(function(data) {
                document.getElementById('current-name').textContent = data.name;
                document.getElementById('current-phone').textContent = data.phone || '-';
                
                // If there's an error message, show it in toastr
                if (data.message) {
                    console.log('Current on-call status:', data.message);
                }
            })
            .catch(function(error) {
                console.error('Error loading current on-call:', error);
                document.getElementById('current-name').textContent = 'No one currently on call';
                document.getElementById('current-phone').textContent = '-';
            })
            .finally(() => {
                window.hideAjaxLoader();
            });
    }

    // Load current holidays
    function loadHolidays() {
        if (!document.getElementById('holiday-list')) return;

        window.showAjaxLoader();
        fetch(urls.holidays + "?year=" + currentYear)
            .then(response => response.json())
            .then(function(holidays) {
                var holidayList = document.getElementById('holiday-list');
                holidayList.innerHTML = '';

                if (holidays.length === 0) {
                    holidayList.innerHTML = '<div class="list-group-item text-muted">No holidays defined for ' + currentYear + '</div>';
                    return;
                }

                holidays.forEach(function(holiday) {
                    var item = document.createElement('div');
                    item.className = 'list-group-item d-flex justify-content-between align-items-center';
                    item.innerHTML = `
                        <div>
                            <i class="fas fa-calendar-day me-2"></i>
                            ${holiday.name}
                        </div>
                        <small class="text-muted">${new Date(holiday.date).toLocaleDateString()}</small>
                    `;
                    holidayList.appendChild(item);
                });
            })
            .catch(function(error) {
                console.error('Error loading holidays:', error);
                toastr.error('Error loading holidays');
            })
            .finally(() => {
                window.hideAjaxLoader();
            });
    }
    
    loadCurrentOnCall();
    setInterval(loadCurrentOnCall, 60000);
    
    // Admin functionality
    if (document.getElementById('team-form')) {
        // Team management
        document.getElementById('team-form').onsubmit = function(e) {
            e.preventDefault();
            
            var teamId = document.getElementById('team-id').value;
            var teamName = document.getElementById('team-name').value;
            var teamColor = document.querySelector('input[name="team-color"]:checked').value;
            
            var data = {
                name: teamName,
                color: teamColor
            };
            
            var method = teamId ? 'PUT' : 'POST';
            var url = teamId ? 
                urls.teams + '/' + teamId :
                urls.teams;
            
            window.showAjaxLoader();    
            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                return response.json().then(data => {
                    if (!response.ok) {
                        throw new Error(data.error || 'Network response was not ok');
                    }
                    return data;
                });
            })
            .then(function(data) {
                toastr.success('Team saved successfully');
                location.reload();  // Refresh to update team list
            })
            .catch(function(error) {
                console.error('Error:', error);
                toastr.error('Error saving team: ' + error.message);
            })
            .finally(() => {
                window.hideAjaxLoader();
            });
        };
        
        window.editTeam = function(teamId) {
            window.showAjaxLoader();
            fetch(urls.teams + '/' + teamId)
                .then(response => {
                    return response.json().then(data => {
                        if (!response.ok) {
                            throw new Error(data.error || 'Failed to load team');
                        }
                        return data;
                    });
                })
                .then(function(team) {
                    document.getElementById('team-id').value = team.id;
                    document.getElementById('team-name').value = team.name;
                    document.getElementById('color-' + team.color).checked = true;
                    document.getElementById('team-modal-title').textContent = 'Edit Team';
                    new bootstrap.Modal(document.getElementById('teamModal')).show();
                })
                .catch(function(error) {
                    console.error('Error:', error);
                    toastr.error('Error loading team: ' + error.message);
                })
                .finally(() => {
                    window.hideAjaxLoader();
                });
        };
        
        window.deleteTeam = function(teamId) {
            if (confirm('Are you sure you want to delete this team?')) {
                window.showAjaxLoader();
                fetch(urls.teams + '/' + teamId, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                    }
                })
                .then(function(response) {
                    if (response.ok) {
                        toastr.success('Team deleted successfully');
                        location.reload();  // Refresh to update team list
                    } else {
                        return response.json().then(data => {
                            throw new Error(data.error || 'Failed to delete team');
                        });
                    }
                })
                .catch(function(error) {
                    console.error('Error:', error);
                    toastr.error('Error deleting team: ' + error.message);
                })
                .finally(() => {
                    window.hideAjaxLoader();
                });
            }
        };
        
        // Schedule upload
        var uploadForm = document.getElementById('upload-form');
        var uploadModal = document.getElementById('uploadModal');
        var bsUploadModal = new bootstrap.Modal(uploadModal);
        
        uploadForm.onsubmit = function(e) {
            e.preventDefault();
            
            var formData = new FormData(this);
            var fileInput = document.getElementById('file');
            var file = fileInput.files[0];
            var autoGenerate = document.getElementById('auto_generate').checked;

            // Basic file validation
            if (!file) {
                toastr.error('Please select a file to upload');
                return;
            }

            if (!file.name.toLowerCase().endsWith('.csv')) {
                toastr.error('Please select a CSV file');
                return;
            }

            // Add CSRF token to formData
            var csrfToken = document.querySelector('input[name="csrf_token"]').value;
            formData.append('csrf_token', csrfToken);
            
            // Set auto_generate to 'true' or 'false' string (JavaScript boolean format)
            formData.set('auto_generate', autoGenerate ? 'true' : 'false');
            
            window.showAjaxLoader();
            fetch(urls.upload, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(function(response) {
                return response.json().then(data => {
                    if (!response.ok) {
                        throw new Error(data.error || 'Upload failed');
                    }
                    return data;
                });
            })
            .then(function(data) {
                console.log('Upload successful:', data);
                toastr.success(data.message || 'Schedule uploaded successfully');
                
                // Reset form and close modal first
                uploadForm.reset();
                bsUploadModal.hide();
                
                // Update calendar after a short delay to allow modal to close
                setTimeout(() => {
                    updateCalendar();
                    loadCurrentOnCall();
                }, 500);
            })
            .catch(function(error) {
                console.error('Upload error:', error);
                toastr.error(error.message || 'An error occurred while uploading the file');
            })
            .finally(() => {
                window.hideAjaxLoader();
            });
        };

        // Holiday upload
        var holidayForm = document.getElementById('holiday-form');
        var holidayModal = document.getElementById('holidayModal');
        var bsHolidayModal = new bootstrap.Modal(holidayModal);

        holidayForm.onsubmit = function(e) {
            e.preventDefault();
            
            var formData = new FormData(this);
            var fileInput = document.getElementById('holiday-file');
            var file = fileInput.files[0];

            if (!file) {
                toastr.error('Please select a file to upload');
                return;
            }

            if (!file.name.toLowerCase().endsWith('.csv')) {
                toastr.error('Please select a CSV file');
                return;
            }

            window.showAjaxLoader();
            fetch(urls.uploadHolidays, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: formData
            })
            .then(function(response) {
                return response.json().then(data => {
                    if (!response.ok) {
                        throw new Error(data.error || 'Upload failed');
                    }
                    return data;
                });
            })
            .then(function(data) {
                console.log('Holiday upload successful:', data);
                toastr.success(data.message || 'Holidays uploaded successfully');
                
                // Reset form
                holidayForm.reset();
                
                // Reload holidays and calendar
                loadHolidays();
                updateCalendar();
            })
            .catch(function(error) {
                console.error('Holiday upload error:', error);
                toastr.error(error.message || 'An error occurred while uploading holidays');
            })
            .finally(() => {
                window.hideAjaxLoader();
            });
        };

        // Reset forms when modals are hidden
        uploadModal.addEventListener('hidden.bs.modal', function() {
            uploadForm.reset();
            // Reset template visibility
            document.getElementById('manual-template').style.display = 'block';
            document.getElementById('auto-template').style.display = 'none';
            document.getElementById('csv-help-text').textContent = 'Required columns: week, name, phone';
        });

        holidayModal.addEventListener('show.bs.modal', function() {
            loadHolidays();
        });
    }
    
    // Initial calendar render
    updateCalendar();
});
