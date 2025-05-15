// Initialize charts on HOD dashboard
function initCharts() {
    // Event status chart
    const eventStatusCtx = document.getElementById('eventStatusChart');
    if (eventStatusCtx) {
        const eventStatusData = JSON.parse(eventStatusCtx.getAttribute('data-chart'));
        
        new Chart(eventStatusCtx, {
            type: 'pie',
            data: {
                labels: Object.keys(eventStatusData),
                datasets: [{
                    data: Object.values(eventStatusData),
                    backgroundColor: [
                        'rgba(255, 193, 7, 0.8)',  // pending - warning
                        'rgba(40, 167, 69, 0.8)',  // approved - success
                        'rgba(220, 53, 69, 0.8)',  // rejected - danger
                        'rgba(23, 162, 184, 0.8)'  // completed - info
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Event Status Distribution',
                        color: '#adb5bd'
                    }
                }
            }
        });
    }

    // Outpass status chart
    const outpassStatusCtx = document.getElementById('outpassStatusChart');
    if (outpassStatusCtx) {
        const outpassStatusData = JSON.parse(outpassStatusCtx.getAttribute('data-chart'));
        
        new Chart(outpassStatusCtx, {
            type: 'pie',
            data: {
                labels: Object.keys(outpassStatusData),
                datasets: [{
                    data: Object.values(outpassStatusData),
                    backgroundColor: [
                        'rgba(255, 193, 7, 0.8)',  // pending - warning
                        'rgba(40, 167, 69, 0.8)',  // approved - success
                        'rgba(220, 53, 69, 0.8)'   // rejected - danger
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Out Pass Status Distribution',
                        color: '#adb5bd'
                    }
                }
            }
        });
    }

    // Events by day of week chart
    const eventsByDayCtx = document.getElementById('eventsByDayChart');
    if (eventsByDayCtx) {
        const eventsByDayData = JSON.parse(eventsByDayCtx.getAttribute('data-chart'));
        const days = Object.keys(eventsByDayData);
        const counts = Object.values(eventsByDayData);
        
        new Chart(eventsByDayCtx, {
            type: 'bar',
            data: {
                labels: days,
                datasets: [{
                    label: 'Number of Events',
                    data: counts,
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Events by Day of Week',
                        color: '#adb5bd'
                    }
                }
            }
        });
    }

    // Outpasses per day chart for security dashboard
    const outpassesByDayCtx = document.getElementById('outpassesByDayChart');
    if (outpassesByDayCtx) {
        const dateLabels = JSON.parse(outpassesByDayCtx.getAttribute('data-labels'));
        const outpassCounts = JSON.parse(outpassesByDayCtx.getAttribute('data-counts'));
        
        new Chart(outpassesByDayCtx, {
            type: 'line',
            data: {
                labels: dateLabels,
                datasets: [{
                    label: 'Approved Out Passes',
                    data: outpassCounts,
                    backgroundColor: 'rgba(32, 201, 151, 0.2)',
                    borderColor: 'rgba(32, 201, 151, 1)',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Approved Out Passes (Last Week)',
                        color: '#adb5bd'
                    }
                }
            }
        });
    }

    // Attendance statistics chart
    const attendanceChartCtx = document.getElementById('attendanceChart');
    if (attendanceChartCtx) {
        const totalRegistrations = parseInt(attendanceChartCtx.getAttribute('data-registrations'));
        const totalAttended = parseInt(attendanceChartCtx.getAttribute('data-attended'));
        const totalAbsent = parseInt(attendanceChartCtx.getAttribute('data-absent'));
        
        new Chart(attendanceChartCtx, {
            type: 'doughnut',
            data: {
                labels: ['Attended', 'Absent', 'Only Registered'],
                datasets: [{
                    data: [
                        totalAttended, 
                        totalAbsent, 
                        totalRegistrations - totalAttended - totalAbsent
                    ],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',  // attended - success
                        'rgba(220, 53, 69, 0.8)',  // absent - danger
                        'rgba(108, 117, 125, 0.8)' // registered - secondary
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Attendance Statistics',
                        color: '#adb5bd'
                    }
                }
            }
        });
    }
}

// Initialize charts when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initCharts);

// Auto-refresh charts every 5 minutes
setInterval(function() {
    initCharts();
}, 5 * 60 * 1000);
