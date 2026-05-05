let datasetLoaded = false;

function switchTab(tabId, element) {
    // Update nav links
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    if (element) {
        element.classList.add('active');
    }

    // Update content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    document.getElementById(tabId).classList.remove('hidden');

    // Load dataset if not loaded yet
    if (tabId === 'dataset-tab' && !datasetLoaded) {
        loadDataset();
    }
}

async function loadDataset() {
    try {
        const response = await fetch('/api/dataset');
        const data = await response.json();
        
        if (response.ok) {
            const thead = document.getElementById('dataset-head');
            const tbody = document.getElementById('dataset-body');
            
            thead.innerHTML = data.columns.map(col => `<th>${col}</th>`).join('');
            
            tbody.innerHTML = data.data.map(row => {
                return `<tr>${data.columns.map(col => `<td>${row[col]}</td>`).join('')}</tr>`;
            }).join('');
            
            datasetLoaded = true;
        } else {
            document.getElementById('dataset-body').innerHTML = `<tr><td colspan="9" style="text-align: center; color: red;">Failed to load dataset: ${data.error}</td></tr>`;
        }
    } catch (error) {
        document.getElementById('dataset-body').innerHTML = `<tr><td colspan="9" style="text-align: center; color: red;">Failed to connect to server.</td></tr>`;
    }
}

document.getElementById('prediction-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('predict-btn');
    const originalText = btn.innerText;
    btn.innerText = 'Analyzing...';
    btn.disabled = true;

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();
        
        if (response.ok) {
            displayResults(result);
        } else {
            alert(result.error || 'Something went wrong');
        }
    } catch (error) {
        alert('Failed to connect to the server');
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

function displayResults(data) {
    const resultSection = document.getElementById('results-section');
    const badge = document.getElementById('prediction-result');
    const precautionsContainer = document.getElementById('precautions-container');
    const precautionsList = document.getElementById('precautions-list');
    const foodsList = document.getElementById('foods-avoid-list');

    resultSection.classList.remove('hidden');
    
    if (data.is_diabetic) {
        badge.className = 'result-badge high-risk';
        badge.innerHTML = `⚠️ High Risk Detected (${(data.probability * 100).toFixed(1)}%)`;
        
        precautionsContainer.classList.remove('hidden');
        
        precautionsList.innerHTML = data.precautions.map(p => `<li>${p}</li>`).join('');
        foodsList.innerHTML = data.foods_to_avoid.map(f => `<li>${f}</li>`).join('');
    } else {
        badge.className = 'result-badge low-risk';
        badge.innerHTML = `✅ Low Risk Detected (${((1 - data.probability) * 100).toFixed(1)}%)`;
        precautionsContainer.classList.add('hidden');
    }
}

document.getElementById('food-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('check-food-btn');
    const input = document.getElementById('food_name');
    const originalText = btn.innerText;
    btn.innerText = 'Analyzing...';
    btn.disabled = true;

    try {
        const response = await fetch('/check-food', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ food_name: input.value }),
        });

        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('food-result-section').classList.remove('hidden');
            document.getElementById('analyzed-food-name').innerText = result.food;
            
            // Parse AI Output
            let text = result.advice;
            let verdict = "UNKNOWN";
            let reasoning = text;
            let alternatives = "No alternatives provided.";

            const verdictMatch = text.match(/VERDICT:\s*(.*)/i);
            const reasoningMatch = text.match(/REASONING:\s*(.*)/i);
            const alternativesMatch = text.match(/ALTERNATIVES:\s*(.*)/i);

            if (verdictMatch) verdict = verdictMatch[1].trim().toUpperCase();
            if (reasoningMatch) reasoning = reasoningMatch[1].trim();
            if (alternativesMatch) alternatives = alternativesMatch[1].trim();

            // Set Badge
            const badgeEl = document.getElementById('food-badge');
            if (verdict.includes("SAFE")) {
                badgeEl.className = 'food-verdict-badge verdict-safe';
                badgeEl.innerText = '✅ SAFE TO EAT';
            } else if (verdict.includes("AVOID")) {
                badgeEl.className = 'food-verdict-badge verdict-avoid';
                badgeEl.innerText = '❌ AVOID';
            } else {
                badgeEl.className = 'food-verdict-badge verdict-moderate';
                badgeEl.innerText = '⚠️ MODERATION REQUIRED';
            }

            document.getElementById('food-reasoning').innerText = reasoning;
            
            // Create list from comma separated alternatives
            const altList = alternatives.split(',').map(a => a.trim()).filter(a => a);
            document.getElementById('food-alternatives').innerHTML = altList.map(a => `<li>${a}</li>`).join('');

        } else {
            alert(result.error || 'Something went wrong');
        }
    } catch (error) {
        alert('Failed to connect to the server');
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});
