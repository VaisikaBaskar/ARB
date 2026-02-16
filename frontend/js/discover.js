const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    // document.getElementById('discoverBtn').addEventListener('click', discoverRecipes);
});

window.discoverRecipes = async function (userId) {
    if (!userId) userId = window.currentUserId;
    const grid = document.getElementById('resultsGrid');
    const seasonInfo = document.getElementById('seasonInfo');
    const btn = document.getElementById('discoverBtn');

    if (!userId) {
        // alert("Please enter a User ID.");
        return;
    }

    // Bind button
    if (btn) btn.onclick = () => window.discoverRecipes(userId);

    // Reset UI
    grid.innerHTML = '<p>Loading...</p>';
    btn.disabled = true;
    btn.textContent = 'Searching...';

    try {
        const response = await fetch(`${API_BASE}/discover/${userId}`);

        if (!response.ok) throw new Error('Discovery failed');

        const data = await response.json();

        // Update Season Header
        const season = data.season || 'Current Season';
        seasonInfo.textContent = `Suggestions for ${season.charAt(0).toUpperCase() + season.slice(1)}`;

        const recipes = data.external_recipes || [];

        if (recipes.length === 0) {
            grid.innerHTML = '<p>No new recipes found at this time.</p>';
            return;
        }

        grid.innerHTML = '';
        recipes.forEach(r => {
            const card = createCard(r);
            grid.appendChild(card);
        });

    } catch (error) {
        console.error(error);
        grid.innerHTML = '<p style="color:red">Error fetching recipes.</p>';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Find New Recipes';
    }
}

function createCard(recipe) {
    const div = document.createElement('div');
    div.className = 'recipe-card';

    // Seasonal Badge
    let badgeHtml = '';
    if (recipe.seasonal_relevance) {
        badgeHtml = '<div class="seasonal-badge">Seasonal Pick</div>';
    }

    // Match Bar
    const match = recipe.match_percent || 0;

    // Missing Ingredients
    const missing = recipe.missing_ingredients || [];
    let missingHtml = '';
    let toggleBtn = '';

    if (missing.length > 0) {
        const listItems = missing.map(m => `<li>${m}</li>`).join('');
        missingHtml = `<ul class="missing-list" id="missing-${Math.random().toString(36).substr(2, 9)}">${listItems}</ul>`;
        // Toggle Logic is handled via onclick below specific to this instance ID or using class
        // Let's keep it simple: just show logic inline or button to toggle visibility
    }

    div.innerHTML = `
        ${badgeHtml}
        <h3>${recipe.name}</h3>
        <p><strong>Cuisine:</strong> ${recipe.cuisine || 'Global'}</p>
        
        <div style="margin-top:10px;">
            <div style="display:flex; justify-content:space-between; font-size:0.9em;">
                <span>Pantry Match</span>
                <span>${match}%</span>
            </div>
            <div class="match-bar-container">
                <div class="match-bar" style="width: ${match}%"></div>
            </div>
        </div>

        ${missing.length > 0 ? `
            <div style="margin-top:10px;">
                <p style="font-size:0.9em; margin:0;">Missing ${missing.length} item(s)</p>
                <button class="toggle-missing" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'block' ? 'none' : 'block'">Details</button>
                <ul class="missing-list" style="display:none;">
                    ${missing.map(m => `<li>${m}</li>`).join('')}
                </ul>
            </div>
        ` : '<p style="font-size:0.9em; color:green; margin-top:10px;">You have all ingredients!</p>'}

        <span class="source-tag">Source: ${recipe.source}</span>
        
        <button onclick="alert('Use Manage Recipes page to add this manually.')" style="width:100%; margin-top:10px; font-size:0.9em; background:#6c757d;">Save Idea</button>
    `;

    return div;
}
