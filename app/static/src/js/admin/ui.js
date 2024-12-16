/**
 * Admin UI Module
 * Handles UI components and their updates
 */

export class AdminUI {
    /**
     * Update system details section
     * @param {Object} data - System metrics data
     */
    updateSystemDetails(data) {
        // CPU Details
        const cpuDetails = document.getElementById('cpuDetails');
        if (cpuDetails) {
            cpuDetails.innerHTML = this.generateCpuDetailsHtml(data.cpu);
        }

        // Memory Details
        const memoryDetails = document.getElementById('memoryDetails');
        if (memoryDetails) {
            memoryDetails.innerHTML = this.generateMemoryDetailsHtml(data.memory);
        }

        // Network Details
        const networkDetails = document.getElementById('networkDetails');
        if (networkDetails) {
            networkDetails.innerHTML = this.generateNetworkDetailsHtml(data.network);
        }
    }

    /**
     * Update system information
     * @param {Object} data - System information data
     */
    updateSystemInfo(data) {
        // Update uptime
        const uptimeInfo = document.getElementById('uptimeInfo');
        if (uptimeInfo) {
            const valueElement = uptimeInfo.querySelector('.system-info-value');
            if (valueElement) {
                valueElement.textContent = `${data.uptime.days}d ${data.uptime.hours}h ${data.uptime.minutes}m`;
            }
        }

        // Update load averages
        ['1', '5', '15'].forEach(minutes => {
            const element = document.getElementById(`loadAvg${minutes}`);
            if (element) {
                const valueElement = element.querySelector('.system-info-value');
                if (valueElement) {
                    valueElement.textContent = data.load_average[`${minutes}min`].toFixed(2);
                }
            }
        });
    }

    /**
     * Update process details
     * @param {Object} data - Process data
     */
    updateProcessDetails(data) {
        const processDetails = document.getElementById('processDetails');
        if (processDetails) {
            processDetails.innerHTML = this.generateProcessDetailsHtml(data);
        }
    }

    /**
     * Update user activity details
     * @param {Object} data - User activity data
     */
    updateUserActivityDetails(data) {
        const userActivityDetails = document.getElementById('userActivityDetails');
        if (userActivityDetails) {
            userActivityDetails.innerHTML = this.generateUserActivityDetailsHtml(data);
        }
    }

    /**
     * Update health status indicators
     * @param {Object} data - Health status data
     */
    updateHealthStatus(data) {
        if (!data.components) return;
        
        Object.entries(data.components).forEach(([component, status]) => {
            const element = document.querySelector(`[data-component="${component}"]`);
            if (element) {
                // Update indicator class
                element.className = `health-indicator health-${status.status}`;
                
                // Update progress bar if exists
                const progressBar = element.closest('.info-box')?.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = `${status.value}%`;
                    progressBar.className = `progress-bar bg-${status.status}`;
                }
                
                // Update value display if exists
                const valueElement = element.closest('.info-box')?.querySelector('.info-box-number');
                if (valueElement) {
                    valueElement.textContent = `${status.value}%`;
                }
            }
        });
    }

    /**
     * Generate CPU details HTML
     * @param {Object} cpu - CPU metrics data
     * @returns {string} Generated HTML
     */
    generateCpuDetailsHtml(cpu) {
        return `
            <div class="detail-item">
                <span class="detail-label">Physical Cores:</span>
                <span class="detail-value">${cpu.count}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Logical Cores:</span>
                <span class="detail-value">${cpu.count_logical}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Per-Core Usage:</span>
                <span class="detail-value">
                    ${cpu.per_core.map((usage, index) => `
                        <span class="core-usage">
                            Core ${index + 1}: ${usage.toFixed(1)}%
                            <div class="progress inline-progress">
                                <div class="progress-bar bg-info" style="width: ${usage}%"></div>
                            </div>
                        </span>
                    `).join('')}
                </span>
            </div>
        `;
    }

    /**
     * Generate memory details HTML
     * @param {Object} memory - Memory metrics data
     * @returns {string} Generated HTML
     */
    generateMemoryDetailsHtml(memory) {
        const totalMemoryGB = (memory.total / (1024 * 1024 * 1024)).toFixed(2);
        const usedMemoryGB = (memory.used / (1024 * 1024 * 1024)).toFixed(2);
        const availableMemoryGB = (memory.available / (1024 * 1024 * 1024)).toFixed(2);
        const swapUsedGB = (memory.swap_used / (1024 * 1024 * 1024)).toFixed(2);
        
        return `
            <div class="detail-item">
                <span class="detail-label">Total Memory:</span>
                <span class="detail-value">${totalMemoryGB} GB</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Used Memory:</span>
                <div class="memory-stat">
                    <span>${usedMemoryGB} GB</span>
                    <div class="progress">
                        <div class="progress-bar bg-warning" style="width: ${memory.percent}%"></div>
                    </div>
                    <span>${memory.percent}%</span>
                </div>
            </div>
            <div class="detail-item">
                <span class="detail-label">Available Memory:</span>
                <span class="detail-value">${availableMemoryGB} GB</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Swap Used:</span>
                <div class="memory-stat">
                    <span>${swapUsedGB} GB</span>
                    <div class="progress">
                        <div class="progress-bar bg-info" style="width: ${memory.swap_percent}%"></div>
                    </div>
                    <span>${memory.swap_percent}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Generate network details HTML
     * @param {Object} network - Network metrics data
     * @returns {string} Generated HTML
     */
    generateNetworkDetailsHtml(network) {
        const uploadSpeed = network.upload_speed_mb;
        const downloadSpeed = network.download_speed_mb;
        const totalSpeed = uploadSpeed + downloadSpeed;
        const baseSpeed = 100; // 100 Mbps base speed
        const utilization = Math.min((totalSpeed / baseSpeed) * 100, 100);

        return `
            <div class="detail-item">
                <span class="detail-label">Network Utilization:</span>
                <div class="network-stat">
                    <span class="speed-value">${utilization.toFixed(1)}%</span>
                    <div class="progress">
                        <div class="progress-bar ${utilization > 85 ? 'bg-danger' : utilization > 70 ? 'bg-warning' : 'bg-success'}" 
                             style="width: ${utilization}%"></div>
                    </div>
                    <span class="speed-total">${totalSpeed.toFixed(2)} / ${baseSpeed} Mbps</span>
                </div>
            </div>
            <div class="detail-item">
                <span class="detail-label">Upload Speed:</span>
                <div class="network-stat">
                    <span class="speed-value">${uploadSpeed.toFixed(2)} MB/s</span>
                    <div class="progress">
                        <div class="progress-bar bg-success" style="width: ${(uploadSpeed / baseSpeed) * 100}%"></div>
                    </div>
                    <span class="speed-total">${(uploadSpeed / baseSpeed * 100).toFixed(1)}% of capacity</span>
                </div>
            </div>
            <div class="detail-item">
                <span class="detail-label">Download Speed:</span>
                <div class="network-stat">
                    <span class="speed-value">${downloadSpeed.toFixed(2)} MB/s</span>
                    <div class="progress">
                        <div class="progress-bar bg-info" style="width: ${(downloadSpeed / baseSpeed) * 100}%"></div>
                    </div>
                    <span class="speed-total">${(downloadSpeed / baseSpeed * 100).toFixed(1)}% of capacity</span>
                </div>
            </div>
        `;
    }

    /**
     * Generate process details HTML
     * @param {Object} process - Process metrics data
     * @returns {string} Generated HTML
     */
    generateProcessDetailsHtml(process) {
        return `
            <div class="detail-item">
                <span class="detail-label">Process CPU Usage:</span>
                <span class="detail-value">${process.cpu_percent.toFixed(1)}%</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Process Memory:</span>
                <span class="detail-value">${this.formatBytes(process.memory_info.rss)}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Threads:</span>
                <span class="detail-value">${process.num_threads}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Open Files:</span>
                <span class="detail-value">${process.open_files}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Active Connections:</span>
                <span class="detail-value">${process.connections}</span>
            </div>
        `;
    }

    /**
     * Generate user activity details HTML
     * @param {Object} data - User activity data
     * @returns {string} Generated HTML
     */
    generateUserActivityDetailsHtml(data) {
        const recentActions = data.recent_actions.slice(0, 5);
        
        return `
            <div class="detail-item">
                <span class="detail-label">Recent Actions:</span>
                <span class="detail-value">${recentActions.length}</span>
            </div>
            ${recentActions.map(action => `
                <div class="detail-item">
                    <span class="detail-label">${new Date(action.timestamp).toLocaleTimeString()}</span>
                    <span class="detail-value">${action.action} by ${action.details}</span>
                </div>
            `).join('')}
        `;
    }

    /**
     * Format bytes to human readable string
     * @param {number} bytes - Number of bytes
     * @param {number} decimals - Number of decimal places
     * @returns {string} Formatted string
     */
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }
}
