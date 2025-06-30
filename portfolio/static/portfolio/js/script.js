// portfolio/static/portfolio/js/script.js

// Declare global variables that will be populated by Django template context
// These variables are injected into the <script> block in stock_calculator.html
// before this script file is loaded.
var isUserAuthenticated;
var canUseCalculatorFreeInitial;
var showLoginPopupInitial;
var userFeedbackMessage;
var loginUrl;
var registerUrl;

$(document).ready(function() {
    // Track if a calculation has been made on the current page load for anonymous users
    var hasCalculatedOnThisPage = false; 

    // Function to disable calculator elements and show popup
    function restrictCalculatorAccess() {
        $('.calculator-input').prop('disabled', true); // Disable all inputs
        $('.calculator-button').prop('disabled', true); // Disable all buttons
        $('#loginSignupModal').modal({
            backdrop: 'static', // Prevent modal from closing when clicking outside
            keyboard: false      // Prevent modal from closing with the escape key
        });
        // Update the user feedback message to reflect restriction
        $('#user-feedback-alert').text("Please login or sign up to continue using the calculator.").removeClass('alert-info').addClass('alert-warning').show();
    }

    // Display initial user feedback message from Django context
    if (userFeedbackMessage) {
        $('#user-feedback-alert').text(userFeedbackMessage).show();
    } else {
        $('#user-feedback-alert').hide(); // Ensure it's hidden if no initial message
    }

    // Initial check on page load: If already restricted by server (e.g., second refresh as anonymous)
    if (!isUserAuthenticated && !canUseCalculatorFreeInitial) {
        restrictCalculatorAccess();
    }

    // --- Your Original Calculator JavaScript Functions ---

    function formatNumber(num) {
        if (isNaN(num) || !isFinite(num)) return '0.00';
        return num.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    function formatCurrency(num) {
        if (isNaN(num) || !isFinite(num)) return '$0.00';
        const formatted = formatNumber(Math.abs(num));
        return (num < 0 ? '-' : '') + '$' + formatted;
    }

    function showError(message) {
        const errorDiv = $('#priceError');
        errorDiv.text(message);
        errorDiv.show();
    }

    function hideError() {
        $('#priceError').hide();
    }

    function toggleCalculationMode() {
        const mode = $('#calculationMode').val();
        if (mode === 'shares') {
            $('#sharesModeInputs').show();
            $('#priceModeInputs').hide();
            hideError();
            calculateFromShares();
        } else {
            $('#sharesModeInputs').hide();
            $('#priceModeInputs').show();
            calculateFromPrice();
        }
        calculateAll(); // Recalculate summary after mode change
    }

    function calculateFromShares() {
        const shares = parseFloat($('#shares').val()) || 0;
        const currentPrice = parseFloat($('#currentPrice').val()) || 0;
        const newShares = parseFloat($('#newShares').val()) || 0;
        const avgBuyPrice = parseFloat($('#avgBuyPrice').val()) || 0;
        
        const costPrice = shares * avgBuyPrice;
        const newCost = newShares * currentPrice;
        $('#newCost').text(formatNumber(newCost));
        $('#calculatedShares').text(newShares.toString());
        
        const totalShares = shares + newShares;
        const totalCost = costPrice + newCost;
        
        $('#totalCost').text(formatNumber(totalCost));
        $('#totalShares').text(totalShares.toString());
        
        if (totalShares > 0) {
            const newAvg = totalCost / totalShares;
            $('#newAvg').text(formatNumber(newAvg));
            $('#summaryNewAvg').text(formatCurrency(newAvg));
            $('#breakEvenPrice').text(formatCurrency(newAvg));
        } else {
            $('#newAvg').text('0.00');
            $('#summaryNewAvg').text('$0.00');
            $('#breakEvenPrice').text('$0.00');
        }
    }

    function calculateFromPrice() {
        const shares = parseFloat($('#shares').val()) || 0;
        const currentPrice = parseFloat($('#currentPrice').val()) || 0;
        const targetAvg = parseFloat($('#targetAvgPrice').val()) || 0;
        const avgBuyPrice = parseFloat($('#avgBuyPrice').val()) || 0;
        const costPrice = shares * avgBuyPrice;
        
        hideError();
        
        if (shares <= 0 || currentPrice <= 0 || avgBuyPrice <= 0) {
            $('#calculatedShares').text('0');
            $('#newCost').text('0.00');
            $('#totalCost').text(formatNumber(costPrice));
            $('#totalShares').text(shares.toString());
            $('#newAvg').text(formatNumber(avgBuyPrice));
            $('#summaryNewAvg').text(formatCurrency(avgBuyPrice));
            $('#breakEvenPrice').text(formatCurrency(avgBuyPrice));
            if (shares === 0 && currentPrice === 0 && avgBuyPrice === 0) {
                 // Do nothing or show a specific message if no initial data
            } else {
                 showError('Please enter valid current holdings (shares, average buy price, current price).');
            }
            return;
        }

        if (targetAvg <= 0) {
            showError('Target average price must be a positive number.');
            $('#calculatedShares').text('N/A');
            $('#newCost').text('N/A');
            return;
        }
        
        const numerator = (targetAvg * shares) - costPrice;
        const denominator = currentPrice - targetAvg;
        
        if (denominator === 0) {
            showError('Target average price cannot be the same as the current price ($' + formatNumber(currentPrice) + ').');
            $('#calculatedShares').text('N/A');
            $('#newCost').text('N/A');
            $('#totalCost').text(formatNumber(costPrice));
            $('#totalShares').text(shares.toString());
            $('#newAvg').text(formatNumber(avgBuyPrice));
            $('#summaryNewAvg').text(formatCurrency(avgBuyPrice));
            $('#breakEvenPrice').text(formatCurrency(avgBuyPrice));
            return;
        }
        
        const requiredShares = numerator / denominator;
        
        if (currentPrice > avgBuyPrice && targetAvg > currentPrice) {
            showError(`To reach a target of $${formatNumber(targetAvg)}, you'd need to sell shares or buy at a higher price than current.`);
            $('#calculatedShares').text('N/A');
            $('#newCost').text('N/A');
            return;
        }
        if (currentPrice < avgBuyPrice && targetAvg < currentPrice) {
            showError(`To reach a target of $${formatNumber(targetAvg)}, your current price must be higher than your target.`);
            $('#calculatedShares').text('N/A');
            $('#newCost').text('N/A');
            return;
        }
        if (requiredShares < 0) {
            showError('Cannot achieve target average by buying more shares at the current price. Your target is too low or too high relative to current price.');
            $('#calculatedShares').text('N/A');
            $('#newCost').text('N/A');
            return;
        }
        
        const requiredSharesRounded = Math.ceil(requiredShares);
        
        const newCost = requiredSharesRounded * currentPrice;
        const totalShares = shares + requiredSharesRounded;
        const totalCost = costPrice + newCost;
        
        const actualNewAvg = totalShares > 0 ? totalCost / totalShares : 0;
        
        $('#calculatedShares').text(requiredSharesRounded.toString());
        $('#newCost').text(formatNumber(newCost));
        $('#totalCost').text(formatNumber(totalCost));
        $('#totalShares').text(totalShares.toString());
        $('#newAvg').text(formatNumber(actualNewAvg));
        $('#summaryNewAvg').text(formatCurrency(actualNewAvg));
        $('#breakEvenPrice').text(formatCurrency(actualNewAvg));
    }

    // Main calculation function, updates all display values based on current inputs
    function calculateAll() {
        const shares = parseFloat($('#shares').val()) || 0;
        const avgPrice = parseFloat($('#avgBuyPrice').val()) || 0;
        const currentPrice = parseFloat($('#currentPrice').val()) || 0;
        const stock = $('#stock').val() || '-';
        
        const costPrice = shares * avgPrice;
        $('#costPrice').text(formatNumber(costPrice));
        
        const currentValue = shares * currentPrice;
        $('#currentValue').text(formatNumber(currentValue));
        
        const pl = currentValue - costPrice;
        const plElement = $('#pl');
        plElement.text(formatNumber(pl));
        
        if (pl < 0) {
            plElement.removeClass('profit-positive').addClass('profit-loss');
        } else {
            plElement.removeClass('profit-loss').addClass('profit-positive');
        }
        
        $('#summaryStock').text(stock);
        $('#summaryPL').text((pl < 0 ? '-' : '+') + formatCurrency(pl));
        
        const mode = $('#calculationMode').val();
        if (mode === 'shares') {
            calculateFromShares();
        } else {
            calculateFromPrice();
        }
    }

    // Function to perform the actual calculation (calls calculateAll after validation)
    // This function is what the 'Calculate Reprice' button will trigger.
    function performCalculationAndRestrict() { // Renamed for clarity in this context
        const shares = parseFloat($('#shares').val());
        const avgBuyPrice = parseFloat($('#avgBuyPrice').val());
        const currentPrice = parseFloat($('#currentPrice').val());
        const calculationMode = $('#calculationMode').val();

        let isValid = true;
        // Basic validation for initial holdings
        if (isNaN(shares) || shares < 0) isValid = false;
        if (isNaN(avgBuyPrice) || avgBuyPrice < 0) isValid = false;
        if (isNaN(currentPrice) || currentPrice < 0) isValid = false; 

        if (calculationMode === 'shares') {
            const newShares = parseFloat($('#newShares').val());
            if (isNaN(newShares) || newShares < 0) isValid = false;
        } else { // price mode
            const targetAvgPrice = parseFloat($('#targetAvgPrice').val());
            if (isNaN(targetAvgPrice) || targetAvgPrice < 0) isValid = false;
        }

        if (!isValid) {
            alert("Please enter valid positive numbers for shares and prices. Current Price can be zero.");
            return; // Stop if inputs are invalid
        }
        
        calculateAll(); // Perform the calculation (updates all display values)

        // For anonymous users: apply restriction after the first valid calculation
        if (!isUserAuthenticated && canUseCalculatorFreeInitial && !hasCalculatedOnThisPage) {
            hasCalculatedOnThisPage = true; // Mark as used on this page
            restrictCalculatorAccess(); // Immediately disable inputs and show modal
        }
    }

    // --- Event Listeners for the Restriction Logic and Calculations ---

    // Bind input events to all relevant calculator inputs for real-time updates
    $('.calculator-input').on('input', function() {
        if (!isUserAuthenticated && (!canUseCalculatorFreeInitial || hasCalculatedOnThisPage)) {
            // If restricted, don't allow live input updates (keep them disabled)
            if (!$('#loginSignupModal').hasClass('in')) { // Only show modal if not already open
                 restrictCalculatorAccess(); 
            }
            return;
        }
        calculateAll(); // For valid/authenticated users, update results live
    });

    // Main Calculate Reprice button click handler
    $('#mainCalculateBtn').click(function() {
        if (isUserAuthenticated) {
            performCalculationAndRestrict(); // Authenticated users have unlimited uses
            return;
        }

        // Anonymous users logic
        if (canUseCalculatorFreeInitial && !hasCalculatedOnThisPage) {
            performCalculationAndRestrict(); // This will perform calculation AND set hasCalculatedOnThisPage = true, then restrict
        } else {
            // Already used once on this page, or restricted by server on load
            restrictCalculatorAccess(); 
        }
    });

    // Main Clear All Inputs button click handler
    $('#mainClearBtn').click(function() {
        if (!isUserAuthenticated && (!canUseCalculatorFreeInitial || hasCalculatedOnThisPage)) {
             // If restricted, don't allow clearing either, just show popup
            restrictCalculatorAccess(); 
            return;
        }
        // Clear inputs
        $('#stock').val('');
        $('#shares').val('');
        $('#avgBuyPrice').val('');
        $('#currentPrice').val('');
        $('#newShares').val('');
        $('#targetAvgPrice').val('');

        // Reset display values
        $('#costPrice').text('0.00').removeClass('profit-loss profit-positive');
        $('#currentValue').text('0.00');
        $('#pl').text('0.00').removeClass('profit-loss profit-positive');
        $('#newAvg').text('0.00');
        $('#totalCost').text('0.00');
        $('#calculatedShares').text('0');
        $('#totalShares').text('0');
        $('#newCost').text('0.00');
        $('#summaryStock').text('-');
        $('#summaryPL').text('$0.00');
        $('#summaryNewAvg').text('$0.00');
        $('#breakEvenPrice').text('$0.00');

        hideError(); // Clear any error messages
        // hasCalculatedOnThisPage is intentionally NOT reset here for anonymous users.
        // The idea is that once they've used their one free calculation on this page load,
        // any further action (even clear) should lead to restriction or require login.
    });

    // Bind change event for calculation mode select
    $('#calculationMode').on('change', toggleCalculationMode);

    // Initialize calculations and mode when page loads (after all elements are ready)
    // This will run calculateAll which itself calls the specific mode calculation (shares/price)
    toggleCalculationMode(); 
});
