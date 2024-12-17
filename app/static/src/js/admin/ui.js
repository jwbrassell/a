/**
 * Admin UI Module
 * Handles UI updates and interactions for admin pages
 */

export class AdminUI {
    constructor() {
        this.healthComponents = ['cpu', 'memory', 'disk', 'network'];
    }

    /**
     * Update health status indicators
     * @param {Object} data - Health status data
     */
    updateHealthStatus(data) {
        if (!data?.components) return;

        // Update component status boxes
        for (const component of this.healthComponents) {
            if (data.components[component]) {
                const status = data.components[component];
                const box = document.querySelector(`.component-${component}`);
                if (box) {
                    // Update value
                    const valueEl = box.querySelector('.info-box-number');
                    if (valueEl) {
                        valueEl.textContent = `${status.value.toFixed(1)}%`;
                    }

                    // Update status color
                    box.className = box.className.replace(/bg-\w+/, `bg-${status.status}`);
                }
            }
        }

        // Update system information
        if (data.system) {
            // Update uptime
            const uptimeEl = document.getElementById('uptimeInfo');
            if (uptimeEl && data.system.uptime) {
                const { days, hours, minutes } = data.system.uptime;
                uptimeEl.textContent = `${days}d ${hours}h ${minutes}m`;
            }

            // Update load averages
            if (data.system.load_average) {
                const loadAvg = data.system.load_average;
                const loadAvg1El = document.getElementById('loadAvg1');
                const loadAvg5El = document.getElementById('loadAvg5');
                const loadAvg15El = document.getElementById('loadAvg15');

                if (loadAvg1El) loadAvg1El.textContent = loadAvg['1min'].toFixed(2);
                if (loadAvg5El) loadAvg5El.textContent = loadAvg['5min'].toFixed(2);
                if (loadAvg15El) loadAvg15El.textContent = loadAvg['15min'].toFixed(2);
            }
        }
    }

    /**
     * Update CPU details
     * @param {Object} data - CPU metrics data
     */
    updateCpuDetails(data) {
        if (!data?.cpu) return;

        const detailsEl = document.getElementById('cpuDetails');
        if (!detailsEl) return;

        const { count, count_logical, per_core } = data.cpu;
        const details = [
            `Physical Cores: ${count}`,
            `Logical Cores: ${count_logical}`,
            'Per Core Usage:',
            ...per_core.map((usage, i) => `Core ${i + 1}: ${usage.toFixed(1)}%`)
        ];

        detailsEl.innerHTML = details.join('<br>');
    }

    /**
     * Update memory details
     * @param {Object} data - Memory metrics data
     */
    updateMemoryDetails(data) {
        if (!data?.memory) return;

        const detailsEl = document.getElementById('memoryDetails');
        if (!detailsEl) return;

        const { total, used, free, swap_total, swap_used } = data.memory;
        const details = [
            `Total: ${this.formatBytes(total)}`,
            `Used: ${this.formatBytes(used)}`,
            `Free: ${this.formatBytes(free)}`,
            'Swap:',
            `  Total: ${this.formatBytes(swap_total)}`,
            `  Used: ${this.formatBytes(swap_used)}`
        ];

        detailsEl.innerHTML = details.join('<br>');
    }

    /**
     * Update network details
     * @param {Object} data - Network metrics data
     */
    updateNetworkDetails(data) {
        if (!data?.network) return;

        const detailsEl = document.getElementById('networkDetails');
        if (!detailsEl) return;

        const { upload_speed_mb, download_speed_mb } = data.network;
        const details = [
            `Upload: ${upload_speed_mb.toFixed(2)} MB/s`,
            `Download: ${download_speed_mb.toFixed(2)} MB/s`
        ];

        detailsEl.innerHTML = details.join('<br>');
    }

    /**
     * Update process details
     * @param {Object} data - Process metrics data
     */
    updateProcessDetails(data) {
        if (!data) return;

        const detailsEl = document.getElementById('processDetails');
        if (!detailsEl) return;

        const details = [
            `CPU Usage: ${data.cpu_percent.toFixed(1)}%`,
            `Memory Usage: ${this.formatBytes(data.memory_info.rss)}`,
            `Threads: ${data.num_threads}`,
            `Open Files: ${data.open_files}`,
            `Connections: ${data.connections}`
        ];

        detailsEl.innerHTML = details.join('<br>');
    }

    /**
     * Format bytes to human readable string
     * @param {number} bytes - Number of bytes
     * @returns {string} Formatted string
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
    }

    /**
     * Show notification
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, error, warning, info)
     */
    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast bg-${type} text-white`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="toast-body">
                ${message}
            </div>
        `;

        const container = document.getElementById('toast-container') || document.body;
        container.appendChild(toast);

        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}
