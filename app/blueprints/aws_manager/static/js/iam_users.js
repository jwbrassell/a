/**
 * IAM User Management
 * ------------------
 * Handles all client-side functionality for AWS IAM users.
 */

let currentUsername = null;

/**
 * Load IAM users from the server
 */
function loadUsers() {
    fetch(window.location.href, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(users => {
        const tbody = document.querySelector('table tbody');
        tbody.innerHTML = '';

        users.forEach(user => {
            const row = `
                <tr>
                    <td>${user.username}</td>
                    <td>${user.user_id}</td>
                    <td>${user.groups.join(', ') || 'None'}</td>
                    <td>${new Date(user.created_date).toLocaleString()}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-info" onclick='viewUserDetails("${user.username}")'>
                                <i class="fas fa-eye"></i> Details
                            </button>
                            <button class="btn btn-sm btn-danger" onclick='confirmDeleteUser("${user.username}")'>
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', row);
        });
    })
    .catch(error => showError('Failed to load users: ' + error.message));
}

/**
 * View user details
 */
function viewUserDetails(username) {
    currentUsername = username;
    fetch(`${window.location.href}/${username}/details`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to load user details');
        }
        return response.json();
    })
    .then(details => {
        // Basic info
        document.getElementById('user-name').textContent = username;
        document.getElementById('user-id').textContent = details.user_id;
        document.getElementById('user-arn').textContent = details.arn;
        document.getElementById('user-created').textContent = 
            new Date(details.created_date).toLocaleString();

        // Groups
        const groupsList = document.getElementById('user-groups');
        groupsList.innerHTML = '';
        details.groups.forEach(group => {
            const li = document.createElement('li');
            li.innerHTML = `
                ${group.GroupName}
                <button class="btn btn-sm btn-danger float-end" 
                        onclick='removeFromGroup("${group.GroupName}")'>
                    <i class="fas fa-times"></i>
                </button>
            `;
            groupsList.appendChild(li);
        });

        // Access Keys
        const keysTable = document.getElementById('access-keys');
        keysTable.innerHTML = '';
        details.access_keys.forEach(key => {
            const row = `
                <tr>
                    <td>${key.AccessKeyId}</td>
                    <td>
                        <span class="badge ${key.Status === 'Active' ? 'badge-success' : 'badge-danger'}">
                            ${key.Status}
                        </span>
                    </td>
                    <td>${new Date(key.CreateDate).toLocaleString()}</td>
                    <td>
                        ${key.Status === 'Active' ? `
                            <button class="btn btn-sm btn-warning" 
                                    onclick="deactivateAccessKey('${key.AccessKeyId}')">
                                Deactivate
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `;
            keysTable.insertAdjacentHTML('beforeend', row);
        });

        // Policies
        const policiesTable = document.getElementById('user-policies');
        policiesTable.innerHTML = '';
        details.policies.forEach(policy => {
            const row = `
                <tr>
                    <td>${policy.PolicyName}</td>
                    <td>${policy.PolicyType}</td>
                    <td>${policy.PolicyArn}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" 
                                onclick='detachPolicy("${policy.PolicyArn}")'>
                            <i class="fas fa-times"></i> Detach
                        </button>
                    </td>
                </tr>
            `;
            policiesTable.insertAdjacentHTML('beforeend', row);
        });

        $('#userDetailsModal').modal('show');
    })
    .catch(error => {
        showError('Failed to load user details: ' + error.message);
    });
}

/**
 * Show create user modal
 */
function showCreateUserModal() {
    document.getElementById('new-username').value = '';
    document.getElementById('create-access-key').checked = true;
    loadAvailablePolicies();
    loadAvailableGroups();
    $('#createUserModal').modal('show');
}

/**
 * Create new IAM user
 */
function createUser() {
    const data = {
        username: document.getElementById('new-username').value,
        create_access_key: document.getElementById('create-access-key').checked,
        policies: Array.from(document.getElementById('new-user-policies').selectedOptions).map(opt => opt.value),
        groups: Array.from(document.getElementById('new-user-groups').selectedOptions).map(opt => opt.value)
    };

    fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to create user');
        return response.json();
    })
    .then(result => {
        $('#createUserModal').modal('hide');
        if (result.access_key) {
            document.getElementById('new-access-key-id').value = result.access_key.AccessKeyId;
            document.getElementById('new-secret-key').value = result.access_key.SecretAccessKey;
            $('#newAccessKeyModal').modal('show');
        }
        showSuccess('User created successfully');
        loadUsers();
    })
    .catch(error => showError('Failed to create user: ' + error.message));
}

/**
 * Confirm and delete user
 */
function confirmDeleteUser(username) {
    if (!confirm(`Are you sure you want to delete user ${username}?`)) return;

    fetch(`${window.location.href}/${username}`, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to delete user');
        showSuccess('User deleted successfully');
        loadUsers();
    })
    .catch(error => showError('Failed to delete user: ' + error.message));
}

/**
 * Load available policies
 */
function loadAvailablePolicies() {
    fetch(`${window.location.href}/policies`)
    .then(response => response.json())
    .then(policies => {
        const select = document.getElementById('new-user-policies');
        select.innerHTML = '';
        policies.forEach(policy => {
            const option = document.createElement('option');
            option.value = policy.PolicyArn;
            option.textContent = `${policy.PolicyName} (${policy.Type})`;
            select.appendChild(option);
        });
    })
    .catch(error => showError('Failed to load policies: ' + error.message));
}

/**
 * Load available groups
 */
function loadAvailableGroups() {
    fetch(`${window.location.href}/groups`)
    .then(response => response.json())
    .then(groups => {
        const select = document.getElementById('new-user-groups');
        select.innerHTML = '';
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.GroupName;
            option.textContent = group.GroupName;
            select.appendChild(option);
        });
    })
    .catch(error => showError('Failed to load groups: ' + error.message));
}

/**
 * Show add policy modal
 */
function showAddPolicyModal() {
    loadAvailablePolicies();
    $('#addPolicyModal').modal('show');
}

/**
 * Attach policy to user
 */
function attachPolicy(policyArn) {
    fetch(`${window.location.href}/${currentUsername}/policies`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            policy_arn: policyArn
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to attach policy');
        $('#addPolicyModal').modal('hide');
        showSuccess('Policy attached successfully');
        viewUserDetails(currentUsername);
    })
    .catch(error => showError('Failed to attach policy: ' + error.message));
}

/**
 * Detach policy from user
 */
function detachPolicy(policyArn) {
    if (!confirm('Are you sure you want to detach this policy?')) return;

    fetch(`${window.location.href}/${currentUsername}/policies/${policyArn}`, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to detach policy');
        showSuccess('Policy detached successfully');
        viewUserDetails(currentUsername);
    })
    .catch(error => showError('Failed to detach policy: ' + error.message));
}

/**
 * Show add group modal
 */
function showAddGroupModal() {
    loadAvailableGroups();
    $('#addGroupModal').modal('show');
}

/**
 * Add user to group
 */
function addToGroup(groupName) {
    fetch(`${window.location.href}/${currentUsername}/groups`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            group_name: groupName
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to add user to group');
        $('#addGroupModal').modal('hide');
        showSuccess('User added to group successfully');
        viewUserDetails(currentUsername);
    })
    .catch(error => showError('Failed to add user to group: ' + error.message));
}

/**
 * Remove user from group
 */
function removeFromGroup(groupName) {
    if (!confirm('Are you sure you want to remove the user from this group?')) return;

    fetch(`${window.location.href}/${currentUsername}/groups/${groupName}`, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to remove user from group');
        showSuccess('User removed from group successfully');
        viewUserDetails(currentUsername);
    })
    .catch(error => showError('Failed to remove user from group: ' + error.message));
}

/**
 * Rotate access key
 */
function rotateAccessKey() {
    if (!confirm('Are you sure you want to rotate this user\'s access key? The old key will be deactivated.')) {
        return;
    }

    fetch(`${window.location.href}/${currentUsername}/rotate-key`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to rotate access key');
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('new-access-key-id').value = data.AccessKeyId;
        document.getElementById('new-secret-key').value = data.SecretAccessKey;
        $('#userDetailsModal').modal('hide');
        $('#newAccessKeyModal').modal('show');
    })
    .catch(error => {
        showError('Failed to rotate access key: ' + error.message);
    });
}

/**
 * Copy access key to clipboard
 */
function copyAccessKey() {
    const accessKeyId = document.getElementById('new-access-key-id').value;
    const secretKey = document.getElementById('new-secret-key').value;
    const text = `Access Key ID: ${accessKeyId}\nSecret Access Key: ${secretKey}`;
    
    navigator.clipboard.writeText(text)
        .then(() => {
            showSuccess('Access key copied to clipboard');
        })
        .catch(() => {
            showError('Failed to copy access key');
        });
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
});
