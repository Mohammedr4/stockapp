  function formatNumber(num) {
            if (isNaN(num) || !isFinite(num)) return '0.00';
            return num.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }

        function formatCurrency(num) {
            if (isNaN(num) || !isFinite(num)) return '$0.00';
            return '$' + formatNumber(Math.abs(num));
        }

        function showError(message) {
            const errorDiv = document.getElementById('priceError');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        function hideError() {
            const errorDiv = document.getElementById('priceError');
            errorDiv.style.display = 'none';
        }

        function toggleCalculationMode() {
            const mode = document.getElementById('calculationMode').value;
            const sharesInputs = document.getElementById('sharesModeInputs');
            const priceInputs = document.getElementById('priceModeInputs');
            
            if (mode === 'shares') {
                sharesInputs.style.display = 'block';
                priceInputs.style.display = 'none';
                hideError();
                calculateFromShares();
            } else {
                sharesInputs.style.display = 'none';
                priceInputs.style.display = 'block';
                calculateFromPrice();
            }
        }

        function calculateFromShares() {
            const shares = parseFloat(document.getElementById('shares').value) || 0;
            const currentPrice = parseFloat(document.getElementById('currentPrice').value) || 0;
            const newShares = parseFloat(document.getElementById('newShares').value) || 0;
            const avgBuyPrice = parseFloat(document.getElementById('avgBuyPrice').value) || 0;
            
            // Calculate cost price first
            const costPrice = shares * avgBuyPrice;
            
            // Calculate new cost
            const newCost = newShares * currentPrice;
            document.getElementById('newCost').textContent = formatNumber(newCost);
            document.getElementById('calculatedShares').textContent = newShares.toString();
            
            // Calculate results
            const totalShares = shares + newShares;
            const totalCost = costPrice + newCost;
            document.getElementById('totalCost').textContent = formatNumber(totalCost);
            document.getElementById('totalShares').textContent = totalShares.toString();
            
            if (totalShares > 0) {
                const newAvg = totalCost / totalShares;
                document.getElementById('newAvg').textContent = formatNumber(newAvg);
                document.getElementById('summaryNewAvg').textContent = formatCurrency(newAvg);
                document.getElementById('breakEvenPrice').textContent = formatCurrency(newAvg);
            }
        }

        function calculateFromPrice() {
            const shares = parseFloat(document.getElementById('shares').value) || 0;
            const currentPrice = parseFloat(document.getElementById('currentPrice').value) || 0;
            const targetAvg = parseFloat(document.getElementById('targetAvgPrice').value) || 0;
            const avgBuyPrice = parseFloat(document.getElementById('avgBuyPrice').value) || 0;
            const costPrice = shares * avgBuyPrice;
            
            hideError();
            
            // Basic validation - check if inputs are valid
            if (shares <= 0 || currentPrice <= 0 || targetAvg <= 0 || avgBuyPrice <= 0) {
                document.getElementById('calculatedShares').textContent = '0';
                document.getElementById('newCost').textContent = '0.00';
                document.getElementById('totalCost').textContent = formatNumber(costPrice);
                document.getElementById('totalShares').textContent = shares.toString();
                document.getElementById('newAvg').textContent = formatNumber(targetAvg);
                document.getElementById('summaryNewAvg').textContent = formatCurrency(targetAvg);
                document.getElementById('breakEvenPrice').textContent = formatCurrency(targetAvg);
                return;
            }
            
            // Calculate required shares using the formula:
            // targetAvg = (costPrice + newShares * currentPrice) / (shares + newShares)
            // Solving for newShares: newShares = (targetAvg * shares - costPrice) / (currentPrice - targetAvg)
            
            const numerator = (targetAvg * shares) - costPrice;
            const denominator = currentPrice - targetAvg;
            
            // Check for division by zero
            if (denominator === 0) {
                showError('Target average price cannot equal current price ($' + formatNumber(currentPrice) + ').');
                document.getElementById('calculatedShares').textContent = 'N/A';
                document.getElementById('newCost').textContent = 'N/A';
                return;
            }
            
            // Calculate required shares
            const requiredShares = numerator / denominator;
            
            // Check if the result makes sense
            if (requiredShares < 0) {
                showError('Cannot achieve target average of $' + formatNumber(targetAvg) + ' by buying more shares. Your target is already higher than what you can achieve by averaging down.');
                document.getElementById('calculatedShares').textContent = 'N/A';
                document.getElementById('newCost').textContent = 'N/A';
                return;
            }
            
            // Round up to whole shares
            const requiredSharesRounded = Math.ceil(requiredShares);
            
            const newCost = requiredSharesRounded * currentPrice;
            const totalShares = shares + requiredSharesRounded;
            const totalCost = costPrice + newCost;
            
            // Calculate the actual new average (might be slightly different due to rounding)
            const actualNewAvg = totalShares > 0 ? totalCost / totalShares : 0;
            
            document.getElementById('calculatedShares').textContent = requiredSharesRounded.toString();
            document.getElementById('newCost').textContent = formatNumber(newCost);
            document.getElementById('totalCost').textContent = formatNumber(totalCost);
            document.getElementById('totalShares').textContent = totalShares.toString();
            document.getElementById('newAvg').textContent = formatNumber(actualNewAvg);
            document.getElementById('summaryNewAvg').textContent = formatCurrency(actualNewAvg);
            document.getElementById('breakEvenPrice').textContent = formatCurrency(actualNewAvg);
        }

        function calculateAll() {
            // Get input values
            const shares = parseFloat(document.getElementById('shares').value) || 0;
            const avgPrice = parseFloat(document.getElementById('avgBuyPrice').value) || 0;
            const currentPrice = parseFloat(document.getElementById('currentPrice').value) || 0;
            const stock = document.getElementById('stock').value || '-';
            
            // Calculate cost price
            const costPrice = shares * avgPrice;
            document.getElementById('costPrice').textContent = formatNumber(costPrice);
            
            // Calculate current value
            const currentValue = shares * currentPrice;
            document.getElementById('currentValue').textContent = formatNumber(currentValue);
            
            // Calculate P&L
            const pl = currentValue - costPrice;
            const plElement = document.getElementById('pl');
            plElement.textContent = formatNumber(pl);
            
            // Update P&L styling
            if (pl < 0) {
                plElement.className = 'display-value profit-loss';
            } else {
                plElement.className = 'display-value profit-positive';
            }
            
            // Update summary
            document.getElementById('summaryStock').textContent = stock;
            document.getElementById('summaryPL').textContent = (pl < 0 ? '-' : '+') + formatCurrency(pl);
            
            // Calculate repricing based on mode
            const mode = document.getElementById('calculationMode').value;
            if (mode === 'shares') {
                calculateFromShares();
            } else {
                calculateFromPrice();
            }
        }

        // Initialize calculations when page loads
        document.addEventListener('DOMContentLoaded', function() {
            calculateAll();
        });