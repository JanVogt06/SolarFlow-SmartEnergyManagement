// Chart Management
class ChartManager {
    constructor() {
        this.powerChart = null;
        this.autarkyChart = null;
        this.powerData = {
            labels: [],
            pv: [],
            load: [],
            grid: []
        };
        this.maxDataPoints = 60; // 60 minutes at 1 minute intervals

        this.initCharts();
    }

    initCharts() {
        // Power Chart
        const powerCtx = document.getElementById('power-chart');
        if (powerCtx) {
            this.powerChart = new Chart(powerCtx, {
                type: 'line',
                data: {
                    labels: this.powerData.labels,
                    datasets: [
                        {
                            label: 'PV-Erzeugung',
                            data: this.powerData.pv,
                            borderColor: '#f59e0b',
                            backgroundColor: 'rgba(245, 158, 11, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Verbrauch',
                            data: this.powerData.load,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Netz',
                            data: this.powerData.grid,
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Leistung (W)'
                            }
                        }
                    }
                }
            });
        }

        // Autarky Gauge
        const autarkyCtx = document.getElementById('autarky-chart');
        if (autarkyCtx) {
            this.autarkyChart = new Chart(autarkyCtx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#10b981', '#e5e7eb'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    circumference: 180,
                    rotation: 270,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: false
                        }
                    }
                }
            });
        }
    }

    updatePowerChart(data) {
        if (!this.powerChart) return;

        const now = new Date();
        const timeLabel = now.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });

        // Add new data
        this.powerData.labels.push(timeLabel);
        this.powerData.pv.push(Math.round(data.pv_power));
        this.powerData.load.push(Math.round(data.load_power));
        this.powerData.grid.push(Math.round(data.grid_power));

        // Keep only last N points
        if (this.powerData.labels.length > this.maxDataPoints) {
            this.powerData.labels.shift();
            this.powerData.pv.shift();
            this.powerData.load.shift();
            this.powerData.grid.shift();
        }

        // Update chart
        this.powerChart.update('none'); // No animation for smoother updates
    }

    updateAutarkyGauge(percentage) {
        if (!this.autarkyChart) return;

        this.autarkyChart.data.datasets[0].data = [percentage, 100 - percentage];

        // Update color based on value
        let color = '#ef4444'; // red
        if (percentage >= 75) {
            color = '#10b981'; // green
        } else if (percentage >= 50) {
            color = '#f59e0b'; // yellow
        }

        this.autarkyChart.data.datasets[0].backgroundColor[0] = color;
        this.autarkyChart.update('none');
    }
}