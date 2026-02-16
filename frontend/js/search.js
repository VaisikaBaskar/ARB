const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('searchBtn').addEventListener('click', performSearch);
    document.getElementById('clearBtn').addEventListener('click', clearFilters);

    // Initial search (empty) to show some results
    performSearch();
});

async function performSearch() {
    const grid = document.getElementById('resultsGrid');
    const resultCount = document.getElementById('resultCount');

    // Collect Inputs
    const ingredient = document.getElementById('ingredient').value.trim();
    const cuisine = document.getElementById('cuisine').value;
    const maxTime = document.getElementById('max_cook_time').value;

    // Checkboxes
    const quick = document.getElementById('quick').checked;
    const healthy = document.getElementById('healthy').checked;
    const budget = document.getElementById('budget').checked;

    // Radio for dietary tag (Single select in Backend API example logic usually, but let's send what we have)
    // The backend `q_tag = request.args.get('dietary_tag')` supports only one tag or iterates?
    // Looking at backend code: `q_tag = request.args.get('dietary_tag')` -> single value. 
    // So UI used Radio buttons correctly.
    // So UI used Radio buttons correctly.
    const dietTag = document.querySelector('input[name="dietary_tag"]:checked').value;

    const userId = window.currentUserId;

    // Build Query Params
    const params = new URLSearchParams();
    if (ingredient) params.append('ingredient', ingredient);
    if (cuisine) params.append('cuisine', cuisine);
    if (maxTime) params.append('max_cook_time', maxTime);
    if (dietTag) params.append('dietary_tag', dietTag);

    if (quick) params.append('quick', 'true');
    if (healthy) params.append('healthy', 'true');
    if (budget) params.append('budget', 'true');

    if (userId) params.append('user_id', userId);

    // Fetch
    grid.innerHTML = '<p>Searching...</p>';

    try {
        const response = await fetch(`${API_BASE}/search?${params.toString()}`);
        if (!response.ok) throw new Error('Search failed');

        const recipes = await response.json();

        resultCount.textContent = `Results (${recipes.length})`;

        if (recipes.length === 0) {
            grid.innerHTML = '<p>No recipes found matching your criteria.</p>';
            return;
        }

        grid.innerHTML = '';
        recipes.forEach(r => {
            const card = createRecipeCard(r);
            grid.appendChild(card);
        });

    } catch (error) {
        console.error(error);
        grid.innerHTML = '<p style="color:red">Error performing search.</p>';
    }
}

function createRecipeCard(recipe) {
    const div = document.createElement('div');
    div.className = 'recipe-card';

    const tags = (recipe.dietary_tags || []).map(t => `<span class="tag">${t}</span>`).join('');
    const ingCount = (recipe.ingredients || []).length;

    div.innerHTML = `
        <h3>${recipe.name}</h3>
        <p><strong>Cuisine:</strong> ${recipe.cuisine || 'Global'}</p>
        <p><strong>Time:</strong> ${recipe.cook_time ? recipe.cook_time + ' mins' : 'N/A'}</p>
        <div style="margin: 10px 0;">${tags}</div>
        <p style="font-size: 0.9em; color: #666;">${ingCount} Ingredients</p>
    `;

    return div;
}

function clearFilters() {
    document.getElementById('ingredient').value = '';
    document.getElementById('cuisine').value = '';
    document.getElementById('max_cook_time').value = '';
    document.querySelector('input[name="dietary_tag"][value=""]').checked = true;
    document.getElementById('quick').checked = false;
    document.getElementById('healthy').checked = false;
    document.getElementById('budget').checked = false;

    performSearch();
}
