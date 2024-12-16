/**
 * Admin Charts Module
 * Handles initialization and updates of all admin dashboard charts
 */

export class AdminCharts {
    constructor() {
        this.charts = {};
    }

    /**
     * Initialize a system metrics chart
     * @param {string} containerId - The ID of the container element
     * @returns {Highcharts.Chart}
     */
    initSystemMetricsChart(containerId) {
        return Highcharts.chart(containerId, {
            chart: { 
                type: 'line',
                backgroundColor: 'transparent'
            },
            title: { text: null },
            xAxis: { type: 'datetime' },
            yAxis: { 
                title: { text: 'Percentage' },
                min: 0,
                max: 100
            },
            legend: {
                align: 'right',
                verticalAlign: 'top',
                layout: 'vertical'
            },
            series: [
                { name: 'CPU', data: [] },
                { name: 'Memory', data: [] }
            ],
            credits: { enabled: false }
        });
    }

    /**
     * Initialize a network metrics chart
     * @param {string} containerId - The ID of the container element
     * @returns {Highcharts.Chart}
     */
    initNetworkMetricsChart(containerId) {
        return Highcharts.chart(containerId, {
            chart: { 
                type: 'area',
                backgroundColor: 'transparent'
            },
            title: { text: null },
            xAxis: { type: 'datetime' },
            yAxis: { 
                title: { text: 'MB/s' },
                min: 0
            },
            legend: {
                align: 'right',
                verticalAlign: 'top',
                layout: 'vertical'
            },
            series: [
                { name: 'Upload', data: [] },
                { name: 'Download', data: [] }
            ],
            credits: { enabled: false }
        });
    }

    /**
     * Initialize a user activity chart
     * @param {string} containerId - The ID of the container element
     * @returns {Highcharts.Chart}
     */
    initUserActivityChart(containerId) {
        return Highcharts.chart(containerId, {
            chart: { 
                type: 'column',
                backgroundColor: 'transparent'
            },
            title: { text: null },
            xAxis: { type: 'datetime' },
            yAxis: { 
                title: { text: 'Count' },
                min: 0
            },
            legend: {
                align: 'right',
                verticalAlign: 'top',
                layout: 'vertical'
            },
            series: [{ name: 'Active Users', data: [] }],
            credits: { enabled: false }
        });
    }

    /**
     * Initialize a response times chart
     * @param {string} containerId - The ID of the container element
     * @returns {Highcharts.Chart}
     */
    initResponseTimesChart(containerId) {
        return Highcharts.chart(containerId, {
            chart: { 
                type: 'line',
                backgroundColor: 'transparent'
            },
            title: { text: null },
            xAxis: { type: 'datetime' },
            yAxis: { title: { text: 'Milliseconds' } },
            legend: {
                align: 'right',
                verticalAlign: 'top',
                layout: 'vertical'
            },
            series: [{ name: 'Average Response Time', data: [] }],
            credits: { enabled: false }
        });
    }

    /**
     * Initialize all charts for a monitoring dashboard
     * @param {Object} containerIds - Object containing chart container IDs
     */
    initializeMonitoringCharts(containerIds) {
        this.charts.systemMetrics = this.initSystemMetricsChart(containerIds.systemMetrics);
        this.charts.networkMetrics = this.initNetworkMetricsChart(containerIds.networkMetrics);
        this.charts.userActivity = this.initUserActivityChart(containerIds.userActivity);
        this.charts.responseTimes = this.initResponseTimesChart(containerIds.responseTimes);
    }

    /**
     * Update system metrics chart with new data
     * @param {Object} data - System metrics data
     */
    updateSystemCharts(data) {
        const now = Date.now();
        
        if (this.charts.systemMetrics) {
            this.charts.systemMetrics.series[0].addPoint(
                [now, data.cpu.percent], 
                true, 
                this.charts.systemMetrics.series[0].data.length > 50
            );
            this.charts.systemMetrics.series[1].addPoint(
                [now, data.memory.percent], 
                true, 
                this.charts.systemMetrics.series[1].data.length > 50
            );
        }

        if (this.charts.networkMetrics) {
            this.charts.networkMetrics.series[0].addPoint(
                [now, data.network.upload_speed_mb], 
                true, 
                this.charts.networkMetrics.series[0].data.length > 50
            );
            this.charts.networkMetrics.series[1].addPoint(
                [now, data.network.download_speed_mb], 
                true, 
                this.charts.networkMetrics.series[1].data.length > 50
            );
        }
    }

    /**
     * Update performance charts with new data
     * @param {Object} data - Performance metrics data
     */
    updatePerformanceCharts(data) {
        if (!data.metrics || !this.charts.responseTimes) return;
        
        const points = data.metrics.map(m => [
            new Date(m.timestamp).getTime(),
            m.response_time
        ]);
        this.charts.responseTimes.series[0].setData(points);
    }

    /**
     * Update user activity chart with new data
     * @param {Object} data - User activity data
     */
    updateUserActivityChart(data) {
        if (!data.hourly_activity || !this.charts.userActivity) return;
        
        const points = data.hourly_activity.map(h => [
            new Date(h.hour).getTime(),
            h.count
        ]);
        this.charts.userActivity.series[0].setData(points);
    }
}
