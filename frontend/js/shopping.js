const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    loadRecipes();
    document.getElementById('generateBtn').addEventListener('click', generateList);
});

async function loadRecipes() {
    const container = document.getElementById('recipeSelection');
    try {
        const response = await fetch(`${API_BASE}/recipes`);
        const recipes = await response.json();

        if (recipes.length === 0) {
            container.innerHTML = '<p>No recipes found.</p>';
            return;
        }

        container.innerHTML = '';
        recipes.forEach(r => {
            const div = document.createElement('div');
            div.className = 'recipe-checkbox';
            div.innerHTML = `
                <input type="checkbox" name="recipe_id" value="${r.recipe_id}" id="r_${r.recipe_id}">
                <label for="r_${r.recipe_id}">${r.name}</label>
            `;
            container.appendChild(div);
        });

    } catch (error) {
        console.error('Error loading recipes:', error);
        container.innerHTML = '<p style="color:red">Error loading recipes.</p>';
    }
}

async function generateList() {
    const userId = window.currentUserId; // Global
    const resultBox = document.getElementById('results');
    const tbody = document.querySelector('#shoppingTable tbody');
    const messageDiv = document.getElementById('message');

    // Get selected IDs
    const checkedBoxes = document.querySelectorAll('input[name="recipe_id"]:checked');
    const recipeIds = Array.from(checkedBoxes).map(cb => cb.value);

    if (!userId) {
        alert('Please log in.');
        return;
    }
    if (recipeIds.length === 0) {
        alert('Please select at least one recipe.');
        return;
    }

    // Reset UI
    resultBox.style.display = 'block';
    tbody.innerHTML = '';
    messageDiv.textContent = 'Generating...';
    messageDiv.style.color = 'blue';

    try {
        const response = await fetch(`${API_BASE}/shopping-list/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipe_ids: recipeIds })
        });

        if (!response.ok) {
            throw new Error('Failed to generate list');
        }

        const data = await response.json();
        const list = data.shopping_list || [];

        messageDiv.textContent = ''; // clear loading

        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">No items needed! You have everything likely available.</td></tr>';
            return;
        }

        let html = '';
        list.forEach(item => {
            let actionClass = '';
            let actionText = item.action.toUpperCase();

            if (item.action === 'buy') actionClass = 'action-buy';
            else if (item.action === 'replace') actionClass = 'action-replace';
            else if (item.action === 'available') actionClass = 'action-available';

            let note = '';
            // Basic warning mapping
            if (item.warning === 'expiring_soon') {
                note = '<span class="warning-badge">Expiring Soon</span>';
            }

            html += `
                <tr>
                    <td style="text-transform: capitalize;">${item.ingredient}</td>
                    <td class="${actionClass}">${actionText}</td>
                    <td>${note}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

    } catch (error) {
        console.error(error);
        messageDiv.textContent = "Error generating list.";
        messageDiv.style.color = "red";
    }
}
