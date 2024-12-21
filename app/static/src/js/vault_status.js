document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts only if Highcharts is loaded
    if (typeof Highcharts !== 'undefined') {
        // Response Time Chart
        Highcharts.chart('responseTimeChart', {
            chart: {
                type: 'line',
                style: {
                    fontFamily: 'Arial, sans-serif'
                }
            },
            title: {
                text: 'Response Time (ms)'
            },
            xAxis: {
                type: 'datetime',
                title: {
                    text: 'Time'
                }
            },
            yAxis: {
                title: {
                    text: 'Response Time (ms)'
                }
            },
            series: [{
                name: 'Response Time',
                data: [] // Will be populated via API
            }]
        });

        // Request Volume Chart
        Highcharts.chart('requestVolumeChart', {
            chart: {
                type: 'column',
                style: {
                    fontFamily: 'Arial, sans-serif'
                }
            },
            title: {
                text: 'Request Volume'
            },
            xAxis: {
                type: 'datetime',
                title: {
                    text: 'Time'
                }
            },
            yAxis: {
                title: {
                    text: 'Requests per Second'
                }
            },
            series: [{
                name: 'Requests',
                data: [] // Will be populated via API
            }]
        });

        // Token Usage Chart
        Highcharts.chart('tokenUsageChart', {
            chart: {
                type: 'area',
                style: {
                    fontFamily: 'Arial, sans-serif'
                }
            },
            title: {
                text: 'Active Token Usage'
            },
            xAxis: {
                type: 'datetime',
                title: {
                    text: 'Time'
                }
            },
            yAxis: {
                title: {
                    text: 'Active Tokens'
                }
            },
            series: [{
                name: 'Active Tokens',
                data: [] // Will be populated via API
            }]
        });
    }

    // Function to fetch and update metrics
    function updateMetrics() {
        if (!window.vault_available) {
            return;
        }

        fetch('/api/vault/metrics')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    console.error('Error fetching metrics:', data.error);
                    return;
                }

                // Update charts if they exist
                const charts = Highcharts.charts;
                if (charts) {
                    // Response Time Chart
                    if (charts[0]) {
                        charts[0].series[0].setData(
                            data.map(point => [
                                new Date(point.timestamp).getTime(),
                                point.response_time
                            ])
                        );
                    }

                    // Request Volume Chart
                    if (charts[1]) {
                        charts[1].series[0].setData(
                            data.map(point => [
                                new Date(point.timestamp).getTime(),
                                point.requests_per_second
                            ])
                        );
                    }

                    // Token Usage Chart
                    if (charts[2]) {
                        charts[2].series[0].setData(
                            data.map(point => [
                                new Date(point.timestamp).getTime(),
                                point.active_tokens
                            ])
                        );
                    }
                }
            })
            .catch(error => {
                console.error('Failed to fetch metrics:', error);
                // Clear charts data on error
                const charts = Highcharts.charts;
                if (charts) {
                    charts.forEach(chart => {
                        if (chart && chart.series[0]) {
                            chart.series[0].setData([]);
                        }
                    });
                }
            });
    }

    // Update metrics initially and every 30 seconds
    if (window.vault_available) {
        updateMetrics();
        setInterval(updateMetrics, 30000);
    }
});
