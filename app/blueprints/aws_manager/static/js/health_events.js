let events = [];
let socket = null;
let notificationPermission = false;
let configId = null;

function initializeHealthEvents(id) {
    configId = id;
    loadEvents();
    initializeWebSocket();
    
    // Check for existing notification permission
    if ('Notification' in window) {
        notificationPermission = Notification.permission === 'granted';
        document.getElementById('enable-browser-notifications').checked = notificationPermission;
    }
}

function initializeWebSocket() {
    socket = io('/health');
    
    socket.on('connect', () => {
        console.log('Connected to health events websocket');
        socket.emit('join', { config_id: configId });
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from health events websocket');
    });
    
    socket.on('health_event', (event) => {
        // Add new event to the list
        events.unshift(event);
        renderEvents();
        
        // Show browser notification if enabled
        if (notificationPermission) {
            showBrowserNotification(event);
        }
    });
    
    socket.on('health_notification', (event) => {
        if (notificationPermission) {
            showBrowserNotification(event);
        }
    });
    
    socket.on('preferences_updated', (preferences) => {
        console.log('Notification preferences updated:', preferences);
    });
}

function loadEvents() {
    fetch(`/aws/configurations/${configId}/health`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        events = data;
        renderEvents();
        updateServicesList(data);
    })
    .catch(error => showError('Failed to load health events: ' + error.message));
}

function renderEvents() {
    const tbody = document.querySelector('#events-table tbody');
    tbody.innerHTML = '';

    const typeFilter = document.getElementById('event-type-filter').value;
    const filteredEvents = typeFilter ? 
        events.filter(event => event.event_type_category.toLowerCase().includes(typeFilter.toLowerCase())) : 
        events;

    filteredEvents.forEach(event => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${event.service}</td>
            <td>${event.event_type_code}</td>
            <td>${event.event_type_category}</td>
            <td>${event.region || 'Global'}</td>
            <td>
                <span class="badge status-badge ${getStatusClass(event.status)}">
                    ${event.status}
                </span>
            </td>
            <td>${new Date(event.start_time).toLocaleString()}</td>
            <td>${event.end_time ? new Date(event.end_time).toLocaleString() : 'Ongoing'}</td>
            <td>
                <button class="btn btn-sm btn-info">
                    <i class="fas fa-info-circle"></i> Details
                </button>
            </td>
        `;
        
        // Add click handler to details button
        row.querySelector('button').addEventListener('click', () => showEventDetails(event));
        tbody.appendChild(row);
    });
}

function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case 'open':
            return 'health-critical';
        case 'upcoming':
            return 'health-warning';
        case 'closed':
            return 'badge-secondary';
        default:
            return 'health-info';
    }
}

function showEventDetails(event) {
    document.getElementById('event-service').textContent = event.service;
    document.getElementById('event-type').textContent = event.event_type_code;
    document.getElementById('event-category').textContent = event.event_type_category;
    document.getElementById('event-region').textContent = event.region || 'Global';
    document.getElementById('event-start-time').textContent = new Date(event.start_time).toLocaleString();
    document.getElementById('event-end-time').textContent = event.end_time ? 
        new Date(event.end_time).toLocaleString() : 'Ongoing';
    document.getElementById('event-status').textContent = event.status;
    document.getElementById('event-description').textContent = event.description;

    const resourcesList = document.getElementById('event-resources');
    resourcesList.innerHTML = '';
    if (event.affected_resources && event.affected_resources.length > 0) {
        event.affected_resources.forEach(resource => {
            const li = document.createElement('li');
            li.textContent = resource;
            resourcesList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'No specific resources affected';
        resourcesList.appendChild(li);
    }

    $('#eventDetailsModal').modal('show');
}

function refreshEvents() {
    fetch(`/aws/configurations/${configId}/health/refresh`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to refresh events');
        }
        return response.json();
    })
    .then(data => {
        showSuccess('Successfully refreshed health events');
        loadEvents();
    })
    .catch(error => {
        showError('Failed to refresh events: ' + error.message);
    });
}

function filterEvents() {
    renderEvents();
}

function showNotificationPreferences() {
    $('#notificationPreferencesModal').modal('show');
}

function updateServicesList(events) {
    const services = new Set(events.map(event => event.service));
    const select = document.getElementById('notify-services');
    select.innerHTML = '';
    
    services.forEach(service => {
        const option = document.createElement('option');
        option.value = service;
        option.textContent = service;
        select.appendChild(option);
    });
}

function saveNotificationPreferences() {
    const preferences = {
        notify_critical: document.getElementById('notify-critical').checked,
        notify_warning: document.getElementById('notify-warning').checked,
        notify_info: document.getElementById('notify-info').checked,
        event_types: Array.from(document.getElementById('notify-event-types').selectedOptions).map(opt => opt.value),
        services: Array.from(document.getElementById('notify-services').selectedOptions).map(opt => opt.value)
    };
    
    socket.emit('set_preferences', preferences);
    
    if (document.getElementById('enable-browser-notifications').checked) {
        requestNotificationPermission();
    }
    
    $('#notificationPreferencesModal').modal('hide');
    showSuccess('Notification preferences saved');
}

function requestNotificationPermission() {
    if (!('Notification' in window)) {
        showError('Browser notifications not supported');
        return;
    }
    
    Notification.requestPermission()
        .then(permission => {
            notificationPermission = permission === 'granted';
            if (!notificationPermission) {
                showError('Notification permission denied');
            }
        });
}

function showBrowserNotification(event) {
    if (!notificationPermission) return;
    
    const title = `AWS Health Event: ${event.service}`;
    const options = {
        body: event.description,
        icon: '/static/vz.png',
        tag: event.event_arn,
        data: event
    };
    
    const notification = new Notification(title, options);
    notification.onclick = function() {
        window.focus();
        showEventDetails(event);
    };
}
