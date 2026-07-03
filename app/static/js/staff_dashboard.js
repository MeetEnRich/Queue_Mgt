document.addEventListener('DOMContentLoaded', function() {
    const dashboardContainer = document.getElementById('staff-dashboard');
    if (!dashboardContainer) return;

    const waitlistBody = document.getElementById('waitlist-tbody');
    const waitingCountEl = document.getElementById('waiting-count');
    const servedCountEl = document.getElementById('served-count');
    const skippedCountEl = document.getElementById('skipped-count');
    const activeTicketCard = document.getElementById('active-ticket-card');
    const callNextBtn = document.getElementById('call-next-btn');

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    let pollInterval;

    function getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        };
    }

    function formatTime(dateTimeStr) {
        if (!dateTimeStr) return '-';
        const date = new Date(dateTimeStr);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    function calculateWait(joinedAtStr) {
        if (!joinedAtStr) return '-';
        const joinedAt = new Date(joinedAtStr);
        const diffMs = new Date() - joinedAt;
        const diffMins = Math.floor(diffMs / 60000);
        return `${diffMins}m ago`;
    }

    function updateDashboard() {
        fetch('/api/staff/waitlist')
            .then(response => {
                if (!response.ok) throw new Error('Unauthorized or network issue');
                return response.json();
            })
            .then(data => {
                // Update stats
                if (waitingCountEl) waitingCountEl.textContent = data.waitlist ? data.waitlist.length : 0;
                if (servedCountEl) servedCountEl.textContent = data.my_served_today || 0;
                if (skippedCountEl) skippedCountEl.textContent = data.my_skipped_today || 0;

                // Call Next button state
                if (callNextBtn) {
                    if (data.waitlist && data.waitlist.length > 0 && !data.currently_serving) {
                        callNextBtn.removeAttribute('disabled');
                        callNextBtn.classList.add('pulse');
                    } else {
                        callNextBtn.setAttribute('disabled', 'true');
                        callNextBtn.classList.remove('pulse');
                    }
                }

                // Update currently serving card
                if (activeTicketCard) {
                    if (data.currently_serving) {
                        const cs = data.currently_serving;
                        activeTicketCard.innerHTML = `
                            <div class="active-ticket-header">
                                <div class="active-ticket-number">#${cs.token_number.toString().padStart(3, '0')}</div>
                                <span class="badge badge--being_served">Being Served</span>
                            </div>
                            <div class="active-ticket-body">
                                <div class="ticket-meta">
                                    <strong>Student:</strong> ${cs.student_name} (${cs.student_matric})<br>
                                    <strong>Department:</strong> ${cs.student_dept}<br>
                                    <strong>Category:</strong> ${cs.complaint_category}<br>
                                    <strong>Description:</strong> <span class="ticket-desc">${cs.complaint_desc}</span>
                                </div>
                                <div class="active-ticket-actions">
                                    <button class="btn btn--success btn--block" id="complete-btn" data-token-id="${cs.id}">
                                        <span class="btn__icon">✓</span> Mark Resolved
                                    </button>
                                    <button class="btn btn--warning btn--block" id="skip-btn" data-token-id="${cs.id}">
                                        <span class="btn__icon">✗</span> Skip Turn
                                    </button>
                                </div>
                            </div>
                        `;
                        // Re-bind actions inside dynamically rendered card
                        document.getElementById('complete-btn').addEventListener('click', handleComplete);
                        document.getElementById('skip-btn').addEventListener('click', handleSkip);
                    } else {
                        activeTicketCard.innerHTML = `
                            <div class="empty-serving-state">
                                <div class="empty-state__icon">📭</div>
                                <h3>No Active Student</h3>
                                <p class="text-secondary">Click "Call Next" when you are ready to attend to the next student in line.</p>
                            </div>
                        `;
                    }
                }

                // Update waitlist table
                if (waitlistBody) {
                    waitlistBody.innerHTML = '';
                    if (data.waitlist && data.waitlist.length > 0) {
                        data.waitlist.forEach(token => {
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td><strong>#${token.token_number.toString().padStart(3, '0')}</strong></td>
                                <td>${token.student_name} <span class="text-muted">(${token.student_matric})</span></td>
                                <td><span class="badge badge--waiting">${token.complaint_category}</span></td>
                                <td class="table-desc-cell" title="${token.complaint_desc}">${token.complaint_desc}</td>
                                <td>${formatTime(token.joined_at)}</td>
                                <td>${calculateWait(token.joined_at)}</td>
                            `;
                            waitlistBody.appendChild(tr);
                        });
                    } else {
                        waitlistBody.innerHTML = `
                            <tr>
                                <td colspan="6" class="data-table__empty">No students waiting in the queue.</td>
                            </tr>
                        `;
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching waitlist:', error);
                // Redirect to login if unauthorized
                if (error.message.includes('Unauthorized')) {
                    clearInterval(pollInterval);
                    window.location.href = '/auth/login';
                }
            });
    }

    function handleCallNext(e) {
        if (e) e.preventDefault();
        callNextBtn.setAttribute('disabled', 'true');
        callNextBtn.classList.remove('pulse');

        fetch('/api/staff/call-next', {
            method: 'POST',
            headers: getHeaders()
        })
        .then(response => response.json())
        .then(data => {
            if (data.token) {
                updateDashboard();
            } else {
                alert(data.error || 'No students waiting or system busy.');
                updateDashboard();
            }
        })
        .catch(error => {
            console.error('Error calling next:', error);
            updateDashboard();
        });
    }

    function handleComplete(e) {
        const tokenId = e.target.closest('button').dataset.tokenId;
        fetch(`/api/staff/complete/${tokenId}`, {
            method: 'POST',
            headers: getHeaders()
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                updateDashboard();
            } else {
                alert(data.error || 'Failed to complete transaction.');
            }
        })
        .catch(error => console.error('Error completing:', error));
    }

    function handleSkip(e) {
        const tokenId = e.target.closest('button').dataset.tokenId;
        if (!confirm('Are you sure you want to skip this student?')) return;
        
        fetch(`/api/staff/skip/${tokenId}`, {
            method: 'POST',
            headers: getHeaders()
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                updateDashboard();
            } else {
                alert(data.error || 'Failed to skip token.');
            }
        })
        .catch(error => console.error('Error skipping:', error));
    }

    // Set up trigger
    if (callNextBtn) {
        callNextBtn.addEventListener('click', handleCallNext);
    }

    // Start polling loop
    pollInterval = setInterval(updateDashboard, 4000);
    updateDashboard(); // Initial load
});
