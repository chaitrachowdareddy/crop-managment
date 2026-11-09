/**
 * Crop Supply Chain Management System - Client Side Scripts
 * Handles live search filters, dynamic calculations, and form validations.
 */

document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------------------
    // 1. Live Table Search Filter
    // -------------------------------------------------------------------------
    const searchInputs = document.querySelectorAll('.table-search-input');
    searchInputs.forEach(function (input) {
        input.addEventListener('keyup', function () {
            const filter = this.value.toLowerCase().trim();
            const targetTableId = this.getAttribute('data-target-table') || 'dataTable';
            const table = document.getElementById(targetTableId);
            
            if (!table) return;

            const rows = table.querySelectorAll('tbody tr');
            let visibleCount = 0;

            rows.forEach(function (row) {
                // If it's a special "no records" row, skip
                if (row.classList.contains('no-records-row')) return;

                const text = row.innerText.toLowerCase();
                if (text.includes(filter)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Handle empty search feedback
            let emptyMsgRow = table.querySelector('.search-empty-feedback');
            if (visibleCount === 0 && filter.length > 0) {
                if (!emptyMsgRow) {
                    const tbody = table.querySelector('tbody');
                    const colSpan = table.querySelectorAll('thead th').length || 6;
                    emptyMsgRow = document.createElement('tr');
                    emptyMsgRow.className = 'search-empty-feedback text-center text-muted py-4';
                    emptyMsgRow.innerHTML = `<td colspan="${colSpan}" class="py-4"><i class="fas fa-search me-2"></i>No matching records found for "<strong>${input.value}</strong>"</td>`;
                    tbody.appendChild(emptyMsgRow);
                }
            } else if (emptyMsgRow) {
                emptyMsgRow.remove();
            }
        });
    });

    // -------------------------------------------------------------------------
    // 2. Dynamic Price Calculator: Total Price = Quantity * Price Per Unit
    // -------------------------------------------------------------------------
    const qtyInput = document.getElementById('calc_quantity') || document.getElementById('quantity');
    const priceInput = document.getElementById('calc_price') || document.getElementById('price_per_unit');
    const totalInput = document.getElementById('calc_total') || document.getElementById('total_price') || document.getElementById('total_amount');

    function calculateTotal() {
        if (qtyInput && priceInput && totalInput) {
            const qty = parseFloat(qtyInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            const total = qty * price;
            totalInput.value = total > 0 ? total.toFixed(2) : '';
        }
    }

    if (qtyInput && priceInput && totalInput) {
        qtyInput.addEventListener('input', calculateTotal);
        priceInput.addEventListener('input', calculateTotal);
    }

    // -------------------------------------------------------------------------
    // 3. Client-Side Form Validations
    // -------------------------------------------------------------------------
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            let isValid = true;

            // Validate phone number if present
            const phoneInput = form.querySelector('input[type="tel"], input[name="phone"], input[name="contact"], input[name="driver_phone"]');
            if (phoneInput && phoneInput.value.trim()) {
                const phoneVal = phoneInput.value.trim().replace(/\D/g, '');
                if (phoneVal.length < 10 || phoneVal.length > 15) {
                    alert('Please enter a valid phone number (at least 10 digits).');
                    phoneInput.focus();
                    isValid = false;
                }
            }

            // Validate numeric positive inputs
            const positiveInputs = form.querySelectorAll('input[type="number"][min="0.01"], input[type="number"][min="1"]');
            positiveInputs.forEach(function (numInput) {
                const val = parseFloat(numInput.value);
                if (isNaN(val) || val <= 0) {
                    alert('Please enter a positive value greater than zero.');
                    numInput.focus();
                    isValid = false;
                }
            });

            if (!isValid || !form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });

    // -------------------------------------------------------------------------
    // 4. Auto-dismiss Flash Alerts after 5 seconds
    // -------------------------------------------------------------------------
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        });
    }, 5000);
});
