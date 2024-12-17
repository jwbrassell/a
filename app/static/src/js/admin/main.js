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

        // Initialize charts
        this.charts.initializeUsersDashboard({
            userActivity: 'userActivityChart',
            roleDistribution: 'roleDistributionChart'
        });

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
            // Fetch user activity data
            const activityData = await this.utils.fetchWithCache('/admin/api/users/dashboard/activity');
            if (activityData.success) {
                this.charts.updateUserActivityChart(activityData.data);
            }

            // Fetch user stats including role distribution
            const statsData = await this.utils.fetchWithCache('/admin/api/users/dashboard/stats');
            if (statsData.success) {
                this.charts.updateRoleDistributionChart(statsData.data);
                this.ui.updateUserStats(statsData.data);
            }

            // Update table data
            await this.refreshTableData();

        } catch (error) {
            console.error('Error refreshing data:', error);
            this.utils.showNotification('Failed to refresh dashboard data', 'error');
        }
    }

    /**
     * Refresh users table data
     */
    async refreshTableData() {
        try {
            const response = await this.utils.fetchWithCache('/admin/api/users');
            if (response.results) {
                const table = $('#usersTable').DataTable();
                table.clear();
                table.rows.add(response.results);
                table.draw();
            }
        } catch (error) {
            console.error('Error refreshing table:', error);
        }
    }

    /**
     * Handle user management actions
     */
    async handleUserAction(action, userId = null, data = {}) {
        try {
            let endpoint = '/admin/api/users';
            let method = 'POST';

            if (action === 'import') {
                // Handle file import
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = '.csv';
                fileInput.click();
                
                fileInput.onchange = async (e) => {
                    const file = e.target.files[0];
                    if (file) {
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        const response = await fetch('/admin/api/users/import', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            this.utils.showNotification('Users imported successfully', 'success');
                            this.refreshData();
                        } else {
                            throw new Error(result.error || 'Import failed');
                        }
                    }
                };
                return;
            }

            if (action === 'export') {
                window.location.href = '/admin/api/users/export';
                return;
            }

            if (userId) {
                endpoint += `/${userId}/${action}`;
                method = action === 'delete' ? 'DELETE' : 'PUT';
            }

            const response = await this.utils.fetchWithCache(endpoint, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }, false);

            if (response.success) {
                this.utils.showNotification('Action completed successfully', 'success');
                // Refresh data after successful action
                this.refreshData();
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
     * Clean up resources
     */
    destroy() {
        this.stopDataRefresh();
        // Clean up any other resources
    }
}
