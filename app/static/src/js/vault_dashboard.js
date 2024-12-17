let currentPolicyName = null;
let currentSecretPath = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    if (window.vault_available) {
        initCharts();
        loadPolicies();
        loadSecrets();
        
        // Refresh data every minute
        setInterval(() => {
            initCharts();
            loadPolicies();
            loadSecrets();
        }, 60000);
    }
});

function initCharts() {
    if (!window.vault_available) return;

    fetch('/api/vault/metrics')
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            const timestamps = data.map(d => d.timestamp);
            const responseTimes = data.map(d => d.response_time);
            const requests = data.map(d => d.requests_per_second);
            const tokens = data.map(d => d.active_tokens);

            // Performance Overview Chart
            Highcharts.chart('performanceChart', {
                chart: { type: 'spline' },
                title: { text: null },
                xAxis: {
                    categories: timestamps,
                    labels: { rotation: -45 }
                },
                yAxis: [{
                    title: { text: 'Response Time (ms)' },
                    opposite: true
                }, {
                    title: { text: 'Requests/Second' }
                }],
                tooltip: {
                    shared: true,
                    crosshairs: true
                },
                series: [{
                    name: 'Response Time',
                    data: responseTimes,
                    color: '#00c0ef',
                    yAxis: 0
                }, {
                    name: 'Requests/Second',
                    data: requests,
                    color: '#00a65a',
                    yAxis: 1
                }]
            });
        })
        .catch(error => console.error('Error loading metrics:', error));
}

function loadPolicies() {
    if (!window.vault_available) return;

    fetch('/api/vault/policies')
        .then(response => response.json())
        .then(policies => {
            if (policies.error) throw new Error(policies.error);

            const rolePolicies = policies.filter(p => p.name.startsWith('role_'));
            const blueprintPolicies = policies.filter(p => p.name.startsWith('blueprint_'));

            // Update role policies table
            const roleTable = document.getElementById('rolePoliciesList');
            roleTable.innerHTML = rolePolicies.map(policy => `
                <tr>
                    <td>${policy.name.replace('role_', '')}</td>
                    <td>${formatPolicyPaths(policy.rules)}</td>
                    <td>
                        <button class="btn btn-info btn-sm" onclick="editPolicy('${policy.name}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deletePolicy('${policy.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');

            // Update blueprint policies table
            const blueprintTable = document.getElementById('blueprintPoliciesList');
            blueprintTable.innerHTML = blueprintPolicies.map(policy => `
                <tr>
                    <td>${policy.name.replace('blueprint_', '')}</td>
                    <td>${formatPolicyPaths(policy.rules)}</td>
                    <td>
                        <button class="btn btn-info btn-sm" onclick="editPolicy('${policy.name}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deletePolicy('${policy.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        })
        .catch(error => console.error('Error loading policies:', error));
}

function formatPolicyPaths(rules) {
    if (typeof rules === 'string') {
        try {
            rules = JSON.parse(rules);
        } catch (e) {
            return 'Invalid policy format';
        }
    }
    return Object.entries(rules.path || {})
        .filter(([path]) => path !== '*') // Skip deny-all rule
        .map(([path, config]) => `${path}: [${config.capabilities.join(', ')}]`)
        .join('<br>');
}

function showCreatePolicyModal() {
    currentPolicyName = null;
    document.getElementById('policyModalTitle').textContent = 'Create Policy';
    document.getElementById('policyForm').reset();
    document.getElementById('policyPaths').innerHTML = `
        <div class="path-entry">
            <div class="form-group">
                <label>Path</label>
                <input type="text" class="form-control path-input" required>
            </div>
            <div class="form-group">
                <label>Capabilities</label>
                <select class="form-control capabilities-select" multiple required>
                    <option value="create">Create</option>
                    <option value="read">Read</option>
                    <option value="update">Update</option>
                    <option value="delete">Delete</option>
                    <option value="list">List</option>
                </select>
            </div>
        </div>
    `;
    $('#policyModal').modal('show');
}

function addPolicyPath() {
    const pathEntry = document.createElement('div');
    pathEntry.className = 'path-entry';
    pathEntry.innerHTML = `
        <div class="form-group">
            <label>Path</label>
            <input type="text" class="form-control path-input" required>
        </div>
        <div class="form-group">
            <label>Capabilities</label>
            <select class="form-control capabilities-select" multiple required>
                <option value="create">Create</option>
                <option value="read">Read</option>
                <option value="update">Update</option>
                <option value="delete">Delete</option>
                <option value="list">List</option>
            </select>
        </div>
        <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove()">
            Remove Path
        </button>
    `;
    document.getElementById('policyPaths').appendChild(pathEntry);
}

function savePolicy() {
    const type = document.getElementById('policyType').value;
    const name = document.getElementById('policyName').value;
    
    const paths = Array.from(document.getElementsByClassName('path-entry')).map(entry => ({
        path: entry.querySelector('.path-input').value,
        capabilities: Array.from(entry.querySelector('.capabilities-select').selectedOptions)
            .map(option => option.value)
    }));

    const data = {
        type: type,
        name: name,
        paths: paths
    };

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch('/api/vault/policies', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) throw new Error(result.error);
        $('#policyModal').modal('hide');
        loadPolicies();
    })
    .catch(error => alert('Error saving policy: ' + error));
}

function editPolicy(name) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch(`/api/vault/policies/${name}`, {
        headers: {
            'X-CSRF-Token': csrfToken
        }
    })
        .then(response => response.json())
        .then(policy => {
            if (policy.error) throw new Error(policy.error);

            currentPolicyName = name;
            document.getElementById('policyModalTitle').textContent = 'Edit Policy';
            document.getElementById('policyType').value = name.startsWith('role_') ? 'role' : 'blueprint';
            document.getElementById('policyName').value = name.replace(/^(role_|blueprint_)/, '');
            
            const pathsContainer = document.getElementById('policyPaths');
            pathsContainer.innerHTML = '';
            
            Object.entries(policy.rules.path || {}).forEach(([path, config]) => {
                if (path === '*') return; // Skip deny-all rule
                
                const pathEntry = document.createElement('div');
                pathEntry.className = 'path-entry';
                pathEntry.innerHTML = `
                    <div class="form-group">
                        <label>Path</label>
                        <input type="text" class="form-control path-input" value="${path}" required>
                    </div>
                    <div class="form-group">
                        <label>Capabilities</label>
                        <select class="form-control capabilities-select" multiple required>
                            <option value="create" ${config.capabilities.includes('create') ? 'selected' : ''}>Create</option>
                            <option value="read" ${config.capabilities.includes('read') ? 'selected' : ''}>Read</option>
                            <option value="update" ${config.capabilities.includes('update') ? 'selected' : ''}>Update</option>
                            <option value="delete" ${config.capabilities.includes('delete') ? 'selected' : ''}>Delete</option>
                            <option value="list" ${config.capabilities.includes('list') ? 'selected' : ''}>List</option>
                        </select>
                    </div>
                    <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove()">
                        Remove Path
                    </button>
                `;
                pathsContainer.appendChild(pathEntry);
            });

            $('#policyModal').modal('show');
        })
        .catch(error => alert('Error loading policy: ' + error));
}

function deletePolicy(name) {
    if (!confirm('Are you sure you want to delete this policy?')) return;

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch(`/api/vault/policies/${name}`, { 
        method: 'DELETE',
        headers: {
            'X-CSRF-Token': csrfToken
        }
    })
        .then(response => response.json())
        .then(result => {
            if (result.error) throw new Error(result.error);
            loadPolicies();
        })
        .catch(error => alert('Error deleting policy: ' + error));
}

function showLDAPConfigModal() {
    document.getElementById('ldapForm').reset();
    $('#ldapModal').modal('show');
}

function saveLDAPConfig() {
    const data = {
        url: document.getElementById('ldapUrlInput').value,
        binddn: document.getElementById('bindDn').value,
        bindpass: document.getElementById('bindPass').value,
        userdn: document.getElementById('userDn').value,
        groupdn: document.getElementById('groupDn').value
    };

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch('/api/vault/ldap/config', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) throw new Error(result.error);
        $('#ldapModal').modal('hide');
        location.reload(); // Refresh to update LDAP status
    })
    .catch(error => alert('Error configuring LDAP: ' + error));
}

function loadSecrets() {
    if (!window.vault_available) return;

    fetch('/api/vault/secrets')
        .then(response => response.json())
        .then(secrets => {
            if (secrets.error) throw new Error(secrets.error);

            const tbody = document.getElementById('secretsList');
            tbody.innerHTML = secrets.map(secret => `
                <tr>
                    <td>${secret.path}</td>
                    <td>${secret.last_modified || 'N/A'}</td>
                    <td>
                        <button class="btn btn-info btn-sm" onclick="viewSecret('${secret.path}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-warning btn-sm" onclick="editSecret('${secret.path}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteSecret('${secret.path}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        })
        .catch(error => console.error('Error loading secrets:', error));
}

function showCreateSecretModal() {
    currentSecretPath = null;
    document.getElementById('secretModalTitle').textContent = 'Create Secret';
    document.getElementById('secretPath').value = '';
    document.getElementById('secretData').value = '';
    document.getElementById('secretPath').disabled = false;
    document.getElementById('secretData').readOnly = false;
    $('#secretModal').modal('show');
}

function viewSecret(path) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch(`/api/vault/secrets/${path}`, {
        headers: {
            'X-CSRF-Token': csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            document.getElementById('secretPath').value = path;
            document.getElementById('secretData').value = JSON.stringify(data, null, 2);
            document.getElementById('secretPath').disabled = true;
            document.getElementById('secretModalTitle').textContent = 'View Secret';
            document.getElementById('secretData').readOnly = true;
            $('#secretModal').modal('show');
        })
        .catch(error => alert('Error loading secret: ' + error));
}

function editSecret(path) {
    currentSecretPath = path;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch(`/api/vault/secrets/${path}`, {
        headers: {
            'X-CSRF-Token': csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            
            document.getElementById('secretPath').value = path;
            document.getElementById('secretData').value = JSON.stringify(data, null, 2);
            document.getElementById('secretPath').disabled = true;
            document.getElementById('secretModalTitle').textContent = 'Edit Secret';
            document.getElementById('secretData').readOnly = false;
            $('#secretModal').modal('show');
        })
        .catch(error => alert('Error loading secret: ' + error));
}

function deleteSecret(path) {
    if (!confirm('Are you sure you want to delete this secret?')) return;

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch(`/api/vault/secrets/${path}`, { 
        method: 'DELETE',
        headers: {
            'X-CSRF-Token': csrfToken
        }
    })
        .then(response => response.json())
        .then(result => {
            if (result.error) throw new Error(result.error);
            loadSecrets();
        })
        .catch(error => alert('Error deleting secret: ' + error));
}

function saveSecret() {
    const path = document.getElementById('secretPath').value;
    let data;
    try {
        data = JSON.parse(document.getElementById('secretData').value);
    } catch (e) {
        alert('Invalid JSON data');
        return;
    }

    const method = currentSecretPath ? 'PUT' : 'POST';
    const url = currentSecretPath ? 
        `/api/vault/secrets/${currentSecretPath}` : 
        `/api/vault/secrets/${path}`;

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    fetch(url, {
        method: method,
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) throw new Error(result.error);
        $('#secretModal').modal('hide');
        loadSecrets();
    })
    .catch(error => alert('Error saving secret: ' + error));
}
