document.addEventListener('DOMContentLoaded', function() {
    const statusContainer = document.getElementById('status-container');
    if (!statusContainer) return;

    const tokenId = statusContainer.dataset.tokenId;
    const officeSlug = statusContainer.dataset.officeSlug;
    if (!tokenId) return;

    const positionEl = document.getElementById('queue-position');
    const waitTimeEl = document.getElementById('wait-time');
    const statusBadgeEl = document.getElementById('status-badge');
    const currentlyServingEl = document.getElementById('currently-serving');
    const cancelBtn = document.getElementById('cancel-queue-btn');
    const alertModal = document.getElementById('turn-alert-modal');
    const alertCloseBtn = document.getElementById('alert-modal-close');

    let currentStatus = statusContainer.dataset.initialStatus || 'waiting';
    let pollInterval;

    // Web Audio API beep sound when called
    function playBeep() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
            gainNode.gain.setValueAtTime(0.5, audioCtx.currentTime);

            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.3); // 300ms beep
        } catch (e) {
            console.error('Audio beep failed to play:', e);
        }
    }

    function updateBadge(status) {
        if (!statusBadgeEl) return;
        statusBadgeEl.className = 'badge';
        statusBadgeEl.textContent = status.replace('_', ' ');
        
        if (status === 'waiting') {
            statusBadgeEl.classList.add('badge--waiting');
        } else if (status === 'being_served') {
            statusBadgeEl.classList.add('badge--being_served');
        } else if (status === 'completed') {
            statusBadgeEl.classList.add('badge--completed');
        } else if (status === 'skipped') {
            statusBadgeEl.classList.add('badge--skipped');
        } else if (status === 'cancelled') {
            statusBadgeEl.classList.add('badge--cancelled');
        }
    }

    function pollStatus() {
        fetch(`/api/queue/status/${tokenId}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response not ok');
                return response.json();
            })
            .then(data => {
                // Update position
                if (positionEl) {
                    if (data.status === 'waiting') {
                        positionEl.textContent = data.position;
                    } else if (data.status === 'being_served') {
                        positionEl.textContent = 'Now!';
                    } else {
                        positionEl.textContent = '-';
                    }
                }

                // Update estimated wait time
                if (waitTimeEl) {
                    if (data.status === 'waiting') {
                        const mins = Math.ceil(data.estimated_wait_seconds / 60);
                        waitTimeEl.textContent = `~${mins} min${mins !== 1 ? 's' : ''}`;
                    } else if (data.status === 'being_served') {
                        waitTimeEl.textContent = 'Being served';
                    } else {
                        waitTimeEl.textContent = '-';
                    }
                }

                // Update currently serving
                if (currentlyServingEl) {
                    if (data.currently_serving) {
                        currentlyServingEl.textContent = `#${data.currently_serving.toString().padStart(3, '0')}`;
                        if (data.currently_serving_counter) {
                            currentlyServingEl.textContent += ` at Counter ${data.currently_serving_counter}`;
                        }
                    } else {
                        currentlyServingEl.textContent = 'None';
                    }
                }

                // Check status change
                if (data.status !== currentStatus) {
                    const prevStatus = currentStatus;
                    currentStatus = data.status;
                    updateBadge(currentStatus);

                    if (currentStatus === 'being_served') {
                        playBeep();
                        if (alertModal) {
                            alertModal.classList.add('active');
                        }
                        // Change background card color or add glowing animation
                        statusContainer.classList.add('serving-glow');
                    }

                    if (['completed', 'skipped', 'cancelled'].includes(currentStatus)) {
                        clearInterval(pollInterval);
                        if (cancelBtn) cancelBtn.style.display = 'none';
                        setTimeout(() => {
                            window.location.reload();
                        }, 3000); // Reload after 3s to show completion screen
                    }
                }
            })
            .catch(error => console.error('Error polling status:', error));
    }

    // Start polling
    if (['waiting', 'being_served'].includes(currentStatus)) {
        pollInterval = setInterval(pollStatus, 5000);
        pollStatus(); // Initial call
    }

    // Cancel queue handling
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!confirm('Are you sure you want to leave the queue?')) return;

            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            fetch(`/api/queue/cancel/${tokenId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.ok) {
                    clearInterval(pollInterval);
                    alert('Queue cancelled successfully.');
                    window.location.href = '/';
                } else {
                    alert('Failed to cancel queue: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => console.error('Error cancelling queue:', error));
        });
    }

    if (alertCloseBtn && alertModal) {
        alertCloseBtn.addEventListener('click', function() {
            alertModal.classList.remove('active');
        });
    }
});
