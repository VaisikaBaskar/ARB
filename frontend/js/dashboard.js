const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    // document.getElementById('loadBtn').addEventListener('click', loadDashboard); // Bound below
});

window.loadDashboard = async function (userId) {
    if (!userId) userId = window.currentUserId;
    const contentDiv = document.getElementById('dashboardContent');
    const msg = document.getElementById('systemMsg');

    if (!userId) {
        // msg.textContent = "Please enter a User ID.";
        return;
    }

    // Bind refresh button if not already
    const btn = document.getElementById('loadBtn');
    if (btn) btn.onclick = () => window.loadDashboard(userId);

    msg.textContent = "Loading data...";
    msg.style.color = "blue";
    contentDiv.style.display = 'none';

    try {
        // Parallel Fetch for efficiency
        const [metricsRes, outcomesRes] = await Promise.all([
            fetch(`${API_BASE}/metrics/${userId}`),
            fetch(`${API_BASE}/outcomes/${userId}`)
        ]);

        if (!metricsRes.ok || !outcomesRes.ok) {
            throw new Error("Failed to fetch dashboard data. Ensure backend is running and user exists.");
        }

        const metrics = await metricsRes.json();
        const outcomes = await outcomesRes.json();

        renderDashboard(metrics, outcomes);

        msg.textContent = `Dashboard loaded for user: ${userId}`;
        msg.style.color = "green";
        contentDiv.style.display = 'block';

    } catch (error) {
        console.error(error);
        msg.textContent = "Error loading dashboard. Check connection or User ID.";
        msg.style.color = "red";
    }
}

function renderDashboard(metrics, outcomes) {
    // Helper to percentage
    const toPct = (val) => (val * 100).toFixed(0) + '%';
    const toDec = (val) => val.toFixed(1);

    // --- Section 1: Recommendations ---
    updateMetric('rec_accuracy', toPct(metrics.recommendation_accuracy || 0));
    updateMetric('avg_rating', metrics.average_rating ? metrics.average_rating + '/5' : 'N/A');
    updateMetric('variety_score', toDec(metrics.variety_score || 0));

    // --- Section 2: Pantry ---
    updateMetric('pantry_util', toPct(metrics.pantry_utilization_rate || 0));
    updateMetric('waste_rate', toPct(metrics.waste_rate || 0));

    // Outcomes logic for waste reduced
    // Structure: food_waste_reduced: { avoided_items: 2, ... }
    const wasteItems = outcomes.food_waste_reduced ? outcomes.food_waste_reduced.avoided_items : 0;
    updateMetric('waste_reduced', wasteItems);

    // --- Section 3: Outcomes ---
    // Time saved
    const minsSaved = outcomes.time_saved ? outcomes.time_saved.estimated_minutes : 0;
    updateMetric('time_saved', minsSaved + 'm');

    // Personalization
    updateMetric('personalization', toPct(outcomes.personalization_effectiveness || 0));

    // Intelligence Growth
    // Format usually 0-1 scale, we can scale it to 100 or keep raw
    // Let's show as score out of 100 for impact
    const iScore = (outcomes.intelligence_growth_score || 0) * 100;
    updateMetric('intelligence', iScore.toFixed(0));
}

function updateMetric(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
        // Simple Color Coding Logic based on content
        if (typeof value === 'string' && value.includes('%')) {
            const num = parseInt(value);
            // Example: High accuracy is green, High waste is red
            if (id === 'waste_rate') {
                el.className = 'metric-value ' + (num > 20 ? 'bad-metric' : 'good-metric');
            } else if (id === 'rec_accuracy' || id === 'pantry_util') {
                el.className = 'metric-value ' + (num > 50 ? 'good-metric' : 'neutral-metric');
            }
        }
    }
}
