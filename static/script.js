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
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.remove('hidden');
    }
}

// Utility for typing effect
function typeText(element, text, speed = 15) {
    element.innerHTML = '';
    let i = 0;
    const timer = setInterval(() => {
        if (i < text.length) {
            element.append(text.charAt(i));
            i++;
        } else {
            clearInterval(timer);
        }
    }, speed);
}

// Predict Form
const predictForm = document.getElementById('predict-form');
if (predictForm) {
    predictForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button');
        const originalText = btn.innerText;
        
        btn.innerHTML = 'Processing Clinical Data...';
        btn.disabled = true;

        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            setTimeout(() => {
                displayResults(result);
                btn.innerText = originalText;
                btn.disabled = false;
            }, 600); 
        } catch (error) {
            alert('Server connection error. Please try again.');
            btn.innerText = originalText;
            btn.disabled = false;
        }
    });
}

function displayResults(data) {
    const resultSection = document.getElementById('results-section');
    if (!resultSection) return;

    const badge = document.getElementById('prediction-result');
    const riskLevelText = document.getElementById('risk-level-text');
    const riskDescription = document.getElementById('risk-description');
    const precautionsContainer = document.getElementById('precautions-container');
    const precautionsList = document.getElementById('precautions-list');
    const foodsList = document.getElementById('foods-avoid-list');

    resultSection.classList.remove('hidden');
    if (precautionsContainer) precautionsContainer.classList.remove('hidden');
    
    let badgeClass = 'result-badge';
    let riskDesc = "";

    if (data.risk_level.includes("High")) {
        badgeClass += ' high-risk';
        riskDesc = "Our model indicates a high probability of diabetes symptoms. Immediate clinical consultation is strongly advised.";
    } else if (data.risk_level === "Moderate") {
        badgeClass += ' moderate-risk';
        riskDesc = "There are significant indicators present. We recommend scheduled screening and preventative dietary adjustments.";
    } else {
        badgeClass += ' low-risk';
        riskDesc = "Indicators are within normal clinical ranges. Focus on maintaining your current health routine.";
    }

    if (badge) {
        badge.className = badgeClass;
        badge.innerHTML = `<span>${data.risk_level} Risk Detected</span>`;
    }
    
    if (riskLevelText) typeText(riskLevelText, `${data.risk_level} (Severity Level ${data.severity_level})`);
    if (riskDescription) typeText(riskDescription, riskDesc);
    
    if (precautionsList) precautionsList.innerHTML = data.precautions.map(p => `<li class="animate-fade-in">${p}</li>`).join('');
    if (foodsList) foodsList.innerHTML = data.foods_to_avoid.map(f => `<li class="animate-fade-in">${f}</li>`).join('');

    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Food Form
const foodForm = document.getElementById('food-form');
if (foodForm) {
    foodForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const foodInput = document.getElementById('food-input');
        const btn = e.target.querySelector('button');
        const resultsDiv = document.getElementById('food-results');
        
        if (!foodInput || !btn || !resultsDiv) return;

        btn.innerHTML = 'AI Analyzing...';
        btn.disabled = true;

        try {
            const response = await fetch('/check-food', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ food_name: foodInput.value })
            });
            const data = await response.json();
            
            btn.innerText = 'Analyze Food';
            btn.disabled = false;

            if (data.error) {
                alert(data.error);
                return;
            }

            resultsDiv.classList.remove('hidden');
            const analyzedFoodName = document.getElementById('analyzed-food-name');
            if (analyzedFoodName) analyzedFoodName.innerText = `Analysis for: ${data.food}`;
            
            const adviceParts = data.advice.split('\n');
            let verdict = "MODERATE";
            let reasoning = "";
            let alternatives = [];

            adviceParts.forEach(part => {
                if (part.includes('VERDICT:')) verdict = part.replace('VERDICT:', '').trim();
                if (part.includes('REASONING:')) reasoning = part.replace('REASONING:', '').trim();
                if (part.includes('ALTERNATIVES:')) alternatives = part.replace('ALTERNATIVES:', '').trim().split(',');
            });

            const badge = document.getElementById('food-verdict');
            if (badge) {
                badge.innerText = verdict;
                badge.className = `food-verdict-badge verdict-${verdict.toLowerCase()}`;
            }

            const reasoningEl = document.getElementById('food-reasoning');
            if (reasoningEl) typeText(reasoningEl, reasoning);
            
            const alternativesEl = document.getElementById('food-alternatives');
            if (alternativesEl) alternativesEl.innerHTML = alternatives.map(a => `<li>${a.trim()}</li>`).join('');
            
            resultsDiv.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            alert('AI Service currently unavailable.');
            btn.innerText = 'Analyze Food';
            btn.disabled = false;
        }
    });
}
