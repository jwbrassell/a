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
                backgroundColor: 'transparent',
                zoomType: 'x'
            },
            title: { text: null },
            xAxis: { 
                type: 'datetime',
                title: { text: 'Time' }
            },
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
            tooltip: {
                shared: true,
                crosshairs: true,
                xDateFormat: '%Y-%m-%d %H:%M:%S'
            },
            plotOptions: {
                series: {
                    marker: {
                        enabled: false
                    }
                }
            },
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
                backgroundColor: 'transparent',
                zoomType: 'x'
            },
            title: { text: null },
            xAxis: { 
                type: 'datetime',
                title: { text: 'Time' }
            },
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
            tooltip: {
                shared: true,
                crosshairs: true,
                xDateFormat: '%Y-%m-%d %H:%M:%S'
            },
            plotOptions: {
                area: {
                    marker: {
                        enabled: false
                    },
                    fillOpacity: 0.3
                }
            },
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
                backgroundColor: 'transparent',
                zoomType: 'x'
            },
            title: { text: null },
            xAxis: { 
                type: 'datetime',
                title: { text: 'Hour' }
            },
            yAxis: { 
                title: { text: 'Active Users' },
                min: 0
            },
            tooltip: {
                formatter: function() {
                    return `<b>${Highcharts.dateFormat('%Y-%m-%d %H:00', this.x)}</b><br/>
                            Active Users: ${this.y}`;
                }
            },
            series: [{ 
                name: 'Active Users',
                data: [],
                color: '#3498db'
            }],
            plotOptions: {
                column: {
                    pointPadding: 0.2,
                    borderWidth: 0
                }
            },
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
                backgroundColor: 'transparent',
                zoomType: 'x'
            },
            title: { text: null },
            xAxis: { 
                type: 'datetime',
                title: { text: 'Time' }
            },
            yAxis: { 
                title: { text: 'Milliseconds' },
                min: 0
            },
            legend: {
                align: 'right',
                verticalAlign: 'top',
                layout: 'vertical'
            },
            series: [{ 
                name: 'Average Response Time', 
                data: [] 
            }],
            tooltip: {
                crosshairs: true,
                shared: true,
                xDateFormat: '%Y-%m-%d %H:%M:%S'
            },
            plotOptions: {
                series: {
                    marker: {
                        enabled: false
                    }
                }
            },
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
        if (!data) return;

        if (this.charts.systemMetrics) {
            // Update CPU data
            if (data.historical?.cpu) {
                const cpuData = data.historical.cpu.map(point => [
                    new Date(point.timestamp).getTime(),
                    point.value
                ]);
                this.charts.systemMetrics.series[0].setData(cpuData);
            }

            // Update Memory data
            if (data.historical?.memory) {
                const memoryData = data.historical.memory.map(point => [
                    new Date(point.timestamp).getTime(),
                    point.value
                ]);
                this.charts.systemMetrics.series[1].setData(memoryData);
            }

            // Add current point if available
            if (data.current) {
                const now = Date.now();
                if (data.current.cpu?.percent !== undefined) {
                    this.charts.systemMetrics.series[0].addPoint(
                        [now, data.current.cpu.percent],
                        true,
                        false
                    );
                }
                if (data.current.memory?.percent !== undefined) {
                    this.charts.systemMetrics.series[1].addPoint(
                        [now, data.current.memory.percent],
                        true,
                        false
                    );
                }
            }
        }

        if (this.charts.networkMetrics && data.historical) {
            // Convert bytes to MB/s for historical network data
            const networkSentData = data.historical.network_sent?.map(point => [
                new Date(point.timestamp).getTime(),
                point.value / (1024 * 1024)
            ]) || [];
            const networkRecvData = data.historical.network_recv?.map(point => [
                new Date(point.timestamp).getTime(),
                point.value / (1024 * 1024)
            ]) || [];

            this.charts.networkMetrics.series[0].setData(networkSentData);
            this.charts.networkMetrics.series[1].setData(networkRecvData);

            // Add current point if available
            if (data.current?.network) {
                const now = Date.now();
                this.charts.networkMetrics.series[0].addPoint(
                    [now, data.current.network.upload_speed_mb],
                    true,
                    false
                );
                this.charts.networkMetrics.series[1].addPoint(
                    [now, data.current.network.download_speed_mb],
                    true,
                    false
                );
            }
        }
    }

    /**
     * Update performance charts with new data
     * @param {Object} data - Performance metrics data
     */
    updatePerformanceCharts(data) {
        if (!data || !this.charts.responseTimes) return;
        
        // Update with historical data
        if (data.historical) {
            const points = data.historical.map(point => [
                new Date(point.timestamp).getTime(),
                point.value
            ]);
            this.charts.responseTimes.series[0].setData(points);
        }
    }

    /**
     * Update user activity chart with new data
     * @param {Object} data - User activity data
     */
    updateUserActivityChart(data) {
        if (!data?.hourly_activity || !this.charts.userActivity) return;
        
        const points = data.hourly_activity.map(h => [
            new Date(h.hour).getTime(),
            h.count
        ]);
        this.charts.userActivity.series[0].setData(points);
    }
}
