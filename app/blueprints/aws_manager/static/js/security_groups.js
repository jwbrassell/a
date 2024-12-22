/**
 * Security Groups Management
 * -------------------------
 * Handles all client-side functionality for AWS security groups.
 */

let securityGroups = [];
let currentGroupId = null;
let currentRegion = null;

/**
 * Load security groups from the server
 */
function loadSecurityGroups() {
    const region = document.getElementById('region-filter').value;
    const url = new URL(window.location.href);
    if (region) {
        url.searchParams.append('region', region);
    }

    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        securityGroups = data;
        renderSecurityGroups();
    })
    .catch(error => showError('Failed to load security groups: ' + error.message));
}

/**
 * Render security groups table
 */
function renderSecurityGroups() {
    const tbody = document.querySelector('table tbody');
    tbody.innerHTML = '';

    securityGroups.forEach(group => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${group.group_name}</td>
            <td>${group.group_id}</td>
            <td>${group.description}</td>
            <td>${group.vpc_id}</td>
            <td>${group.region}</td>
            <td>
                <span class="badge badge-info">
                    ${group.inbound_rules.length} inbound
                </span>
                <span class="badge badge-info">
                    ${group.outbound_rules.length} outbound
                </span>
            </td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-info" onclick="viewSecurityGroup('${group.group_id}', '${group.region}')">
                        <i class="fas fa-eye"></i> View Rules
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="confirmDeleteGroup('${group.group_id}', '${group.region}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Show security group details
 */
function viewSecurityGroup(groupId, region) {
    currentGroupId = groupId;
    currentRegion = region;
    
    fetch(`${window.location.href}/${groupId}?region=${region}`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to load security group details');
        }
        return response.json();
    })
    .then(group => {
        document.getElementById('sg-name').textContent = group.group_name;
        document.getElementById('sg-id').textContent = group.group_id;
        document.getElementById('sg-description').textContent = group.description;
        document.getElementById('sg-vpc').textContent = group.vpc_id;
        document.getElementById('sg-region').textContent = group.region;

        renderRules(group.inbound_rules, 'inbound-rules', 'ingress');
        renderRules(group.outbound_rules, 'outbound-rules', 'egress');

        $('#securityGroupModal').modal('show');
    })
    .catch(error => {
        showError('Failed to load security group details: ' + error.message);
    });
}

/**
 * Render security group rules
 */
function renderRules(rules, targetId, ruleType) {
    const tbody = document.getElementById(targetId);
    tbody.innerHTML = '';

    if (rules.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No rules defined</td>
            </tr>
        `;
        return;
    }

    rules.forEach(rule => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${getProtocolName(rule.IpProtocol)}</td>
            <td>${rule.IpProtocol === '-1' ? 'All' : rule.IpProtocol}</td>
            <td>${formatPortRange(rule)}</td>
            <td>${formatSource(rule)}</td>
            <td>${rule.Description || ''}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick='removeRule(${JSON.stringify(rule)}, "${ruleType}")'>
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Show create security group modal
 */
function showCreateGroupModal() {
    document.getElementById('group-name').value = '';
    document.getElementById('group-description').value = '';
    document.getElementById('group-vpc').value = '';
    document.getElementById('group-region').value = document.getElementById('region-filter').value;
    $('#createGroupModal').modal('show');
}

/**
 * Create new security group
 */
function createSecurityGroup() {
    const data = {
        name: document.getElementById('group-name').value,
        description: document.getElementById('group-description').value,
        vpc_id: document.getElementById('group-vpc').value,
        region: document.getElementById('group-region').value
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
        if (!response.ok) throw new Error('Failed to create security group');
        return response.json();
    })
    .then(() => {
        $('#createGroupModal').modal('hide');
        showSuccess('Security group created successfully');
        loadSecurityGroups();
    })
    .catch(error => showError('Failed to create security group: ' + error.message));
}

/**
 * Confirm and delete security group
 */
function confirmDeleteGroup(groupId, region) {
    if (!confirm('Are you sure you want to delete this security group?')) return;

    fetch(`${window.location.href}/${groupId}?region=${region}`, {
        method: 'DELETE',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to delete security group');
        showSuccess('Security group deleted successfully');
        loadSecurityGroups();
    })
    .catch(error => showError('Failed to delete security group: ' + error.message));
}

/**
 * Show add rule modal
 */
function showAddRuleModal(ruleType) {
    document.getElementById('rule-type').value = ruleType;
    document.getElementById('rule-protocol').value = '-1';
    document.getElementById('rule-from-port').value = '';
    document.getElementById('rule-to-port').value = '';
    document.getElementById('rule-cidr').value = '';
    document.getElementById('rule-description').value = '';
    updatePortFields();
    $('#addRuleModal').modal('show');
}

/**
 * Update port fields visibility based on protocol
 */
function updatePortFields() {
    const protocol = document.getElementById('rule-protocol').value;
    const portFields = document.querySelector('.port-range');
    portFields.style.display = protocol === '-1' || protocol === 'icmp' ? 'none' : 'block';
}

/**
 * Add security group rule
 */
function addSecurityRule() {
    const ruleType = document.getElementById('rule-type').value;
    const protocol = document.getElementById('rule-protocol').value;
    const fromPort = document.getElementById('rule-from-port').value;
    const toPort = document.getElementById('rule-to-port').value;
    const cidr = document.getElementById('rule-cidr').value;
    const description = document.getElementById('rule-description').value;

    const rule = {
        IpProtocol: protocol,
        FromPort: protocol === '-1' ? -1 : parseInt(fromPort || -1),
        ToPort: protocol === '-1' ? -1 : parseInt(toPort || fromPort || -1),
        IpRanges: [{
            CidrIp: cidr,
            Description: description
        }]
    };

    fetch(`${window.location.href}/${currentGroupId}/rules`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            rules: [rule],
            rule_type: ruleType,
            region: currentRegion
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to add security rule');
        return response.json();
    })
    .then(() => {
        $('#addRuleModal').modal('hide');
        showSuccess('Security rule added successfully');
        viewSecurityGroup(currentGroupId, currentRegion);
    })
    .catch(error => showError('Failed to add security rule: ' + error.message));
}

/**
 * Remove security group rule
 */
function removeRule(rule, ruleType) {
    if (!confirm('Are you sure you want to remove this rule?')) return;

    fetch(`${window.location.href}/${currentGroupId}/rules`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            rules: [rule],
            rule_type: ruleType,
            region: currentRegion
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to remove security rule');
        return response.json();
    })
    .then(() => {
        showSuccess('Security rule removed successfully');
        viewSecurityGroup(currentGroupId, currentRegion);
    })
    .catch(error => showError('Failed to remove security rule: ' + error.message));
}

/**
 * Helper functions
 */
function getProtocolName(protocol) {
    switch (protocol) {
        case '-1': return 'All Traffic';
        case 'tcp': return 'TCP';
        case 'udp': return 'UDP';
        case 'icmp': return 'ICMP';
        default: return protocol;
    }
}

function formatPortRange(rule) {
    if (rule.IpProtocol === '-1') return 'All';
    if (rule.FromPort === rule.ToPort) return rule.FromPort;
    return `${rule.FromPort}-${rule.ToPort}`;
}

function formatSource(rule) {
    if (rule.IpRanges && rule.IpRanges.length > 0) {
        return rule.IpRanges.map(r => r.CidrIp).join(', ');
    }
    if (rule.UserIdGroupPairs && rule.UserIdGroupPairs.length > 0) {
        return rule.UserIdGroupPairs.map(p => p.GroupId).join(', ');
    }
    return 'None';
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    loadSecurityGroups();
});
