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
        console.log('Initializing monitoring dashboard...');
        
        // Initialize charts
        this.charts.initializeMonitoringCharts({
            systemMetrics: 'systemMetricsChart',
            networkMetrics: 'networkMetricsChart',
            userActivity: 'userActivityChart',
            responseTimes: 'responseTimesChart'
        });

        // Start data refresh - default to 60 seconds (1 minute) to match metrics collection
        this.startDataRefresh(options.refreshInterval || 60000);
    }

    /**
     * Start periodic data refresh
     * @param {number} interval - Refresh interval in milliseconds
     */
    startDataRefresh(interval) {
        console.log('Starting data refresh with interval:', interval);
        
        // Clear any existing interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        // Initial refresh
        this.refreshData();

        // Set up periodic refresh
        this.refreshInterval = setInterval(() => this.refreshData(), interval);
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
            console.log('Refreshing dashboard data...');
            
            // Fetch system resources
            const resourcesResponse = await fetch('/admin/monitoring/api/system-resources');
            console.log('System resources response:', resourcesResponse);
            const resourcesData = await resourcesResponse.json();
            console.log('System resources data:', resourcesData);
            
            if (resourcesData.success) {
                // Update system metrics charts
                this.charts.updateSystemCharts(resourcesData.data);
                // Update CPU and memory details
                this.ui.updateCpuDetails(resourcesData.data.current);
                this.ui.updateMemoryDetails(resourcesData.data.current);
                this.ui.updateNetworkDetails(resourcesData.data.current);
            }

            // Fetch performance metrics
            const performanceResponse = await fetch('/admin/monitoring/api/performance');
            console.log('Performance response:', performanceResponse);
            const performanceData = await performanceResponse.json();
            console.log('Performance data:', performanceData);
            
            if (performanceData.success) {
                this.charts.updatePerformanceCharts(performanceData.data);
                this.ui.updateProcessDetails(performanceData.data.current);
            }

            // Fetch health status
            const healthResponse = await fetch('/admin/monitoring/api/health');
            console.log('Health response:', healthResponse);
            const healthData = await healthResponse.json();
            console.log('Health data:', healthData);
            
            if (healthData.success) {
                this.ui.updateHealthStatus(healthData.data.current);
            }

            // Fetch user activity
            const activityResponse = await fetch('/admin/monitoring/api/user-activity');
            console.log('Activity response:', activityResponse);
            const activityData = await activityResponse.json();
            console.log('Activity data:', activityData);
            
            if (activityData.success) {
                this.charts.updateUserActivityChart(activityData.data);
            }

        } catch (error) {
            console.error('Error refreshing data:', error);
            this.ui.showNotification('Failed to refresh dashboard data', 'error');
        }
    }

    /**
     * Handle alert actions
     */
    async handleAlertAction(action, alertId = null, data = {}) {
        try {
            let endpoint = '/admin/monitoring/api/alerts';
            let method = 'POST';

            if (action === 'create') {
                const form = document.getElementById('newAlertForm');
                const formData = new FormData(form);
                data = Object.fromEntries(formData.entries());
            } else if (alertId) {
                endpoint += `/${alertId}`;
                method = action === 'delete' ? 'DELETE' : 'PUT';
            }

            const response = await fetch(endpoint, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.ui.showNotification('Alert action completed successfully', 'success');
                // Refresh data after successful action
                this.refreshData();
                // Close modal if it exists
                const modal = bootstrap.Modal.getInstance(document.getElementById('newAlertModal'));
                if (modal) {
                    modal.hide();
                }
                return result;
            } else {
                throw new Error(result.error || 'Alert action failed');
            }
        } catch (error) {
            this.ui.showNotification(error.message, 'error');
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
