// AWS Monitor Plugin JavaScript

// Utility functions
function showLoading(element) {
    element.classList.add('spinning');
}

function hideLoading(element) {
    element.classList.remove('spinning');
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-danger border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    document.body.appendChild(toast);
    new bootstrap.Toast(toast).show();
}

// Instance management
function refreshInstances() {
    const refreshBtn = document.querySelector('.refresh-button');
    if (refreshBtn) showLoading(refreshBtn);

    fetch('/api/poll')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                location.reload();
            } else {
                showError(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to refresh instances');
        })
        .finally(() => {
            if (refreshBtn) hideLoading(refreshBtn);
        });
}

function instanceAction(instanceId, action) {
    fetch(`/api/instances/${instanceId}/action`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            setTimeout(refreshInstances, 2000);
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to perform instance action');
    });
}

// Synthetic monitoring
function updateTestChart(testId) {
    fetch(`/api/synthetic/results?test_id=${testId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const ctx = document.getElementById('results-chart').getContext('2d');
                if (window.testChart) window.testChart.destroy();
                
                window.testChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.data.map(r => new Date(r.timestamp).toLocaleTimeString()),
                        datasets: [{
                            label: 'Response Time (ms)',
                            data: data.data.map(r => r.response_time),
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Failed to load test results');
        });
}

// Template management
function launchTemplate(templateId) {
    const form = document.getElementById('launchForm');
    const formData = new FormData(form);
    
    fetch(`/api/templates/${templateId}/launch`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            region: formData.get('region')
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            bootstrap.Modal.getInstance(document.getElementById('launchModal')).hide();
            setTimeout(refreshInstances, 2000);
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Failed to launch instance');
    });
}

// Initialize DataTables
document.addEventListener('DOMContentLoaded', function() {
    const tables = [
        '#instances-table',
        '#tests-table',
        '#templates-table'
    ];
    
    tables.forEach(tableId => {
        const table = document.querySelector(tableId);
        if (table) {
            $(tableId).DataTable({
                pageLength: 10,
                order: [[0, 'asc']],
                columnDefs: [
                    { orderable: false, targets: -1 }
                ]
            });
        }
    });

    // Setup auto-refresh for instances
    setInterval(refreshInstances, 60000);
});
