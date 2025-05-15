// General client-side functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.map(function (tooltip) {
        return new bootstrap.Tooltip(tooltip);
    });

    // Initialize popovers
    var popovers = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popovers.map(function (popover) {
        return new bootstrap.Popover(popover);
    });

    // Auto-hide success and info alerts after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.alert-success, .alert-info').forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Set active navigation item based on current URL
    var currentUrl = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(function(link) {
        var href = link.getAttribute('href');
        if (href === currentUrl || (href !== '/' && currentUrl.startsWith(href))) {
            link.classList.add('active');
        }
    });

    // Handle notification refresh
    const notificationRefreshBtn = document.getElementById('refreshNotifications');
    if (notificationRefreshBtn) {
        notificationRefreshBtn.addEventListener('click', function() {
            fetchNotifications();
        });
    }

    // Setup date and time pickers if they exist
    setupDateTimePickers();
    
    // Initialize any filter dropdowns
    initializeFilters();
});

// Function to fetch latest notifications via AJAX
function fetchNotifications() {
    const notificationContainer = document.getElementById('notificationList');
    const notificationBadge = document.getElementById('notificationBadge');
    
    if (notificationContainer) {
        // Show loading indicator
        notificationContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Fetch notifications
        fetch('/notifications/api')
            .then(response => response.json())
            .then(data => {
                if (data.notifications && data.notifications.length > 0) {
                    // Update notification badge
                    notificationBadge.innerText = data.unread_count;
                    notificationBadge.style.display = data.unread_count > 0 ? 'inline-block' : 'none';
                    
                    // Render notifications
                    let notificationHtml = '';
                    data.notifications.forEach(notification => {
                        notificationHtml += `
                            <a href="${notification.link}" class="list-group-item list-group-item-action ${notification.is_read ? '' : 'list-group-item-primary'}">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">${notification.title}</h6>
                                    <small>${notification.time_ago}</small>
                                </div>
                                <p class="mb-1">${notification.message}</p>
                            </a>
                        `;
                    });
                    notificationContainer.innerHTML = notificationHtml;
                } else {
                    notificationContainer.innerHTML = '<div class="text-center py-3">No notifications</div>';
                    notificationBadge.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
                notificationContainer.innerHTML = '<div class="text-center py-3 text-danger">Failed to load notifications</div>';
            });
    }
}

// Setup date and time pickers
function setupDateTimePickers() {
    // This is a placeholder for a date/time picker implementation
    // In a full implementation, you might use a library like Flatpickr or Bootstrap Datepicker
    
    // For this example, we'll just add validation to the standard HTML date/time inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (!this.value) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    });
    
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (!this.value) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    });
}

// Initialize filter dropdowns
function initializeFilters() {
    const filterDropdowns = document.querySelectorAll('.filter-dropdown');
    filterDropdowns.forEach(dropdown => {
        dropdown.addEventListener('change', function() {
            const filterType = this.dataset.filterType;
            const filterValue = this.value;
            
            document.querySelectorAll(`.filterable`).forEach(item => {
                const itemValue = item.dataset[filterType];
                
                if (filterValue === 'all' || itemValue === filterValue) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
}
