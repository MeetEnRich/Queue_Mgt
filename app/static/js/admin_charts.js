document.addEventListener('DOMContentLoaded', function() {
    const dashboard = document.getElementById('adminDashboard');
    if (!dashboard) return;

    const role = dashboard.dataset.role;
    if (!role) return;

    // Chart.js dark-theme defaults
    if (typeof Chart !== 'undefined') {
        Chart.defaults.color = '#94a3b8'; // text secondary
        Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.1)'; // grid line
        Chart.defaults.font.family = "'Inter', sans-serif";
    } else {
        console.error('Chart.js is not loaded.');
        return;
    }

    const officeSlug = dashboard.dataset.officeSlug;
    if (role === 'office_admin') {
        loadOfficeAnalytics();
    } else if (role === 'super_admin') {
        if (officeSlug) {
            loadSuperOfficeAnalytics(officeSlug);
        } else {
            loadSuperAnalytics();
        }
    }

    function loadOfficeAnalytics() {
        const urlParams = new URLSearchParams(window.location.search);
        const dateFrom = urlParams.get('date_from') || '';
        const dateTo = urlParams.get('date_to') || '';
        
        let apiUrl = '/api/office-admin/analytics';
        if (dateFrom || dateTo) {
            apiUrl += `?date_from=${dateFrom}&date_to=${dateTo}`;
        }

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) throw new Error('Failed to fetch analytics');
                return response.json();
            })
            .then(data => {
                renderHourlyChart(data.hourly_arrivals || []);
                renderCategoryChart(data.by_category || []);
                renderStaffChart(data.staff_leaderboard || []);
            })
            .catch(error => console.error('Error loading office analytics:', error));
    }

    function loadSuperAnalytics() {
        fetch('/api/super-admin/analytics')
            .then(response => {
                if (!response.ok) throw new Error('Failed to fetch analytics');
                return response.json();
            })
            .then(data => {
                renderOfficeComparisonChart(data.offices || []);
            })
            .catch(error => console.error('Error loading super analytics:', error));
    }

    function loadSuperOfficeAnalytics(officeSlug) {
        const urlParams = new URLSearchParams(window.location.search);
        const dateFrom = urlParams.get('date_from') || '';
        const dateTo = urlParams.get('date_to') || '';
        
        let apiUrl = `/api/super-admin/analytics/${officeSlug}`;
        if (dateFrom || dateTo) {
            apiUrl += `?date_from=${dateFrom}&date_to=${dateTo}`;
        }

        fetch(apiUrl)
            .then(response => {
                if (!response.ok) throw new Error('Failed to fetch analytics');
                return response.json();
            })
            .then(data => {
                renderHourlyChart(data.hourly_arrivals || []);
                renderCategoryChart(data.by_category || []);
                renderStaffChart(data.staff_leaderboard || []);
            })
            .catch(error => console.error('Error loading super office analytics:', error));
    }

    function renderHourlyChart(hourlyArrivals) {
        const ctx = document.getElementById('hourlyChart');
        if (!ctx) return;

        // Generate full 24h labels or typical business hours (8-18)
        const hours = Array.from({ length: 11 }, (_, i) => i + 8); // 8 to 18
        const labels = hours.map(h => `${h.toString().padStart(2, '0')}:00`);
        const counts = hours.map(h => {
            const match = hourlyArrivals.find(item => item.hour === h);
            return match ? match.count : 0;
        });

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Arrivals',
                    data: counts,
                    backgroundColor: 'rgba(20, 184, 166, 0.6)', // Teal
                    borderColor: '#14b8a6',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    function renderCategoryChart(byCategory) {
        const ctx = document.getElementById('categoryChart');
        if (!ctx) return;

        if (byCategory.length === 0) {
            ctx.parentNode.innerHTML += '<div class="empty-chart-msg">No data for categories</div>';
            ctx.style.display = 'none';
            return;
        }

        const labels = byCategory.map(c => c.name);
        const counts = byCategory.map(c => c.count);

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        'rgba(20, 184, 166, 0.7)', // Teal
                        'rgba(16, 185, 129, 0.7)', // Emerald
                        'rgba(245, 158, 11, 0.7)', // Amber
                        'rgba(59, 130, 246, 0.7)', // Blue
                        'rgba(239, 68, 68, 0.7)',  // Red
                        'rgba(168, 85, 247, 0.7)'  // Purple
                    ],
                    borderColor: '#1e293b',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: window.innerWidth < 600 ? 'bottom' : 'right',
                        labels: {
                            boxWidth: 12,
                            padding: window.innerWidth < 600 ? 8 : 15
                        }
                    }
                }
            }
        });
    }

    function renderStaffChart(staffLeaderboard) {
        const ctx = document.getElementById('staffChart');
        if (!ctx) return;

        if (staffLeaderboard.length === 0) {
            ctx.parentNode.innerHTML += '<div class="empty-chart-msg">No staff activity recorded</div>';
            ctx.style.display = 'none';
            return;
        }

        const labels = staffLeaderboard.map(s => s.name);
        const served = staffLeaderboard.map(s => s.served);
        const skipped = staffLeaderboard.map(s => s.skipped);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Served',
                        data: served,
                        backgroundColor: 'rgba(16, 185, 129, 0.6)', // Emerald
                        borderColor: '#10b981',
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Skipped',
                        data: skipped,
                        backgroundColor: 'rgba(148, 163, 184, 0.4)', // Slate/Grey
                        borderColor: '#94a3b8',
                        borderWidth: 1,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    function renderOfficeComparisonChart(offices) {
        const ctx = document.getElementById('officeComparisonChart');
        if (!ctx) return;

        const labels = offices.map(o => o.name);
        const served = offices.map(o => o.total_served);
        const waiting = offices.map(o => o.waiting);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Served Today',
                        data: served,
                        backgroundColor: 'rgba(20, 184, 166, 0.6)', // Teal
                        borderColor: '#14b8a6',
                        borderWidth: 1,
                        borderRadius: 4
                    },
                    {
                        label: 'Currently Waiting',
                        data: waiting,
                        backgroundColor: 'rgba(245, 158, 11, 0.6)', // Amber
                        borderColor: '#f59e0b',
                        borderWidth: 1,
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
});
