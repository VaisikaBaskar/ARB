const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    loadRecipes();
    document.getElementById('checkBtn').addEventListener('click', checkMissing);
});

async function loadRecipes() {
    const select = document.getElementById('recipeSelect');
    try {
        const response = await fetch(`${API_BASE}/recipes`);
        const recipes = await response.json();

        if (recipes.length === 0) {
            select.innerHTML = '<option value="">No recipes found</option>';
            return;
        }

        select.innerHTML = '<option value="">-- Select a Recipe --</option>';
        recipes.forEach(r => {
            const option = document.createElement('option');
            option.value = r.recipe_id;
            // Show cuisine if available for better context
            option.textContent = r.name + (r.cuisine ? ` (${r.cuisine})` : '');
            select.appendChild(option);
        });

    } catch (error) {
        console.error('Error loading recipes:', error);
        select.innerHTML = '<option value="">Error loading recipes</option>';
    }
}

async function checkMissing() {
    const userId = window.currentUserId; // Global
    const recipeId = document.getElementById('recipeSelect').value;
    const resultBox = document.getElementById('results');
    const list = document.getElementById('missingList');
    const msg = document.getElementById('statusMsg');

    if (!userId) {
        alert("Please log in.");
        return;
    }
    if (!recipeId) {
        alert('Please select a Recipe.');
        return;
    }

    // Reset UI
    resultBox.style.display = 'block';
    list.innerHTML = '';
    msg.textContent = 'Checking...';
    msg.style.color = 'blue';

    try {
        const response = await fetch(`${API_BASE}/missing-ingredients/${userId}/${recipeId}`);

        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }

        const data = await response.json();
        const missing = data.missing_ingredients || [];

        msg.textContent = ''; // clear loading message

        if (missing.length === 0) {
            msg.textContent = "Great! You have all the ingredients for this recipe.";
            msg.style.color = "green";
        } else {
            msg.textContent = `You are missing ${missing.length} ingredient(s):`;
            msg.style.color = "orange";

            missing.forEach(item => {
                const li = document.createElement('li');
                li.className = 'missing-item';
                li.textContent = item; // Backend returns distinct lower-cased names
                list.appendChild(li);
            });
        }

    } catch (error) {
        console.error(error);
        msg.textContent = "Error checking ingredients. Ensure backend is running.";
        msg.style.color = "red";
    }
}
