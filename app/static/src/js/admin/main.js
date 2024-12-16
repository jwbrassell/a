/**
 * Admin Main Module
 * Provides a clean API for admin pages by combining charts, utils, and UI modules
 */

import { AdminCharts } from './charts.js';
import { AdminUtils } from './utils.js';
import { AdminUI } from './ui.js';

export class Admin {
    constructor() {
        this.charts = new AdminCharts();
        this.utils = new AdminUtils();
        this.ui = new AdminUI();
        this.refreshInterval = null;
    }

    /**
     * Initialize monitoring dashboard
     * @param {Object} options - Dashboard options
     */
    initMonitoringDashboard(options = {}) {
        // Initialize charts
        this.charts.initializeMonitoringCharts({
            systemMetrics: 'systemMetricsChart',
            networkMetrics: 'networkMetricsChart',
            userActivity: 'userActivityChart',
            responseTimes: 'responseTimesChart'
        });

        // Start data refresh
        this.startDataRefresh(options.refreshInterval || 30000);
    }

    /**
     * Initialize users dashboard
     * @param {Object} options - Dashboard options
     */
    initUsersDashboard(options = {}) {
        // Initialize DataTable
        this.utils.initDataTable('#usersTable', {
            responsive: true,
            lengthChange: true,
            autoWidth: false,
            buttons: ["copy", "csv", "excel", "pdf", "print"]
        });

        // Initialize tooltips
        this.utils.initTooltips();

        // Initialize charts if needed
        if (document.getElementById('userActivityChart')) {
            this.charts.initUserActivityChart('userActivityChart');
        }

        // Start data refresh
        this.startDataRefresh(options.refreshInterval || 30000);
    }

    /**
     * Start periodic data refresh
     * @param {number} interval - Refresh interval in milliseconds
     */
    startDataRefresh(interval) {
        this.refreshInterval = setInterval(() => this.refreshData(), interval);
        // Initial refresh
        this.refreshData();
    }

    /**
     * Stop periodic data refresh
     */
    stopDataRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Refresh all dashboard data
     */
    async refreshData() {
        try {
            // Fetch system resources
            const systemData = await this.utils.fetchWithCache('/admin/monitoring/api/system-resources');
            if (systemData.success) {
                this.charts.updateSystemCharts(systemData.data);
                this.ui.updateSystemDetails(systemData.data);
            }

            // Fetch performance metrics
            const perfData = await this.utils.fetchWithCache('/admin/monitoring/api/performance');
            if (perfData.success) {
                this.charts.updatePerformanceCharts(perfData.data);
                this.ui.updateProcessDetails(perfData.data.process);
            }

            // Fetch user activity
            const activityData = await this.utils.fetchWithCache('/admin/monitoring/api/user-activity');
            if (activityData.success) {
                this.charts.updateUserActivityChart(activityData.data);
                this.ui.updateUserActivityDetails(activityData.data);
            }

            // Fetch health status
            const healthData = await this.utils.fetchWithCache('/admin/monitoring/api/health');
            if (healthData.success) {
                this.ui.updateHealthStatus(healthData.data);
                this.ui.updateSystemInfo(healthData.data.system);
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.utils.showNotification('Failed to refresh dashboard data', 'error');
        }
    }

    /**
     * Handle user management actions
     */
    async handleUserAction(action, userId, data = {}) {
        try {
            const endpoint = `/admin/api/users/${userId}/${action}`;
            const response = await this.utils.fetchWithCache(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }, false);

            if (response.success) {
                this.utils.showNotification('Action completed successfully', 'success');
                return response;
            } else {
                throw new Error(response.error || 'Action failed');
            }
        } catch (error) {
            this.utils.showNotification(error.message, 'error');
            throw error;
        }
    }

    /**
     * Handle alert management
     */
    async handleAlertAction(action, alertId = null, data = {}) {
        try {
            let endpoint = '/admin/monitoring/api/alerts';
            let method = 'POST';

            if (alertId) {
                endpoint += `/${alertId}`;
                method = action === 'delete' ? 'DELETE' : 'PUT';
            }

            const response = await this.utils.fetchWithCache(endpoint, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: method !== 'DELETE' ? JSON.stringify(data) : undefined
            }, false);

            if (response.success) {
                this.utils.showNotification('Alert action completed successfully', 'success');
                return response;
            } else {
                throw new Error(response.error || 'Alert action failed');
            }
        } catch (error) {
            this.utils.showNotification(error.message, 'error');
            throw error;
        }
    }

    /**
     * Clean up resources
     */
    destroy() {
        this.stopDataRefresh();
        // Clean up any other resources
    }
}

// Create global admin instance
window.admin = new Admin();
