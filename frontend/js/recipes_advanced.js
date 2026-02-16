const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    loadRecipes();
    addIngredientRow(); // Add one initial empty row

    document.getElementById('addIngredientBtn').addEventListener('click', addIngredientRow);
    document.getElementById('recipeForm').addEventListener('submit', saveRecipe);
});

// --- Dynamic Ingredient Rows ---
function addIngredientRow() {
    const container = document.getElementById('ingredientsContainer');
    const row = document.createElement('div');
    row.className = 'ingredient-row';

    row.innerHTML = `
        <input type="text" placeholder="Ingredient Name" class="ing-name" required>
        <input type="text" placeholder="Quantity (optional)" class="ing-qty">
        <button type="button" class="delete-btn" style="background: #666;" onclick="this.parentElement.remove()">X</button>
    `;
    container.appendChild(row);
}

// --- Load Recipes ---
function loadRecipes() {
    const listDiv = document.getElementById('recipeList');

    fetch(`${API_BASE}/recipes`)
        .then(res => res.json())
        .then(recipes => {
            if (recipes.length === 0) {
                listDiv.innerHTML = '<p>No recipes found.</p>';
                return;
            }

            // Store for modal access
            window.currentRecipes = recipes;

            let html = '';
            recipes.forEach((r, index) => {
                html += `
                    <div class="recipe-item">
                        <div>
                            <strong>${r.name}</strong> (${r.cuisine || 'Unknown'})
                        </div>
                        <div class="actions">
                            <button class="view-btn" onclick="openRecipeModal(${index})" style="margin-right: 10px;">View</button>
                            <button class="delete-btn" onclick="deleteRecipe('${r.recipe_id}')">Delete</button>
                        </div>
                    </div>
                `;
            });
            listDiv.innerHTML = html;
        })
        .catch(err => {
            console.error(err);
            listDiv.innerHTML = '<p style="color:red">Error loading recipes.</p>';
        });
}

// --- Save Recipe ---
function saveRecipe(e) {
    e.preventDefault();

    const messageDiv = document.getElementById('message');
    messageDiv.textContent = 'Saving...';
    messageDiv.style.color = 'blue';

    // Basic Fields
    const recipeId = document.getElementById('recipe_id').value.trim();
    const name = document.getElementById('name').value.trim();
    const cuisine = document.getElementById('cuisine').value.trim();
    const diet = document.getElementById('diet').value.trim();
    const cookTime = document.getElementById('cook_time').value;
    const cookingSteps = document.getElementById('cooking_steps').value.trim();

    // Ingredients (Name + Qty)
    const ingredientRows = document.querySelectorAll('.ingredient-row');
    const ingredients = [];

    ingredientRows.forEach(row => {
        const nameInput = row.querySelector('.ing-name').value.trim();
        const qtyInput = row.querySelector('.ing-qty').value.trim();

        if (nameInput) {
            if (qtyInput) {
                ingredients.push({ name: nameInput, quantity: qtyInput });
            } else {
                ingredients.push(nameInput); // Backwards compatibility for plain strings
            }
        }
    });

    // Dietary Tags
    const tags = [];
    document.querySelectorAll('input[name="dietary_tag"]:checked').forEach(cb => {
        tags.push(cb.value);
    });

    const payload = {
        recipe_id: recipeId,
        name: name,
        cuisine: cuisine,
        diet: diet,
        cook_time: cookTime ? parseInt(cookTime) : 0,
        cooking_steps: cookingSteps,
        ingredients: ingredients,
        dietary_tags: tags
    };

    fetch(`${API_BASE}/recipe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            messageDiv.textContent = data.message || 'Recipe saved!';
            messageDiv.style.color = 'green';
            loadRecipes(); // Refresh list
            e.target.reset(); // Clear form
            document.getElementById('ingredientsContainer').innerHTML = ''; // Clear rows
            addIngredientRow(); // Add one back
        })
        .catch(err => {
            console.error(err);
            messageDiv.textContent = 'Error saving recipe.';
            messageDiv.style.color = 'red';
        });
}

// --- Delete Recipe ---
// Make it global so onclick works
window.deleteRecipe = function (recipeId) {
    if (!confirm('Are you sure you want to delete this recipe?')) return;

    fetch(`${API_BASE}/recipe/${recipeId}`, {
        method: 'DELETE'
    })
        .then(res => {
            if (res.ok) {
                loadRecipes();
            } else {
                alert('Failed to delete recipe.');
            }
        })
        .catch(err => {
            console.error(err);
            alert('Error deleting recipe.');
        });
};

// --- Modal Logic ---
window.openRecipeModal = function (index) {
    const recipe = window.currentRecipes ? window.currentRecipes[index] : null;
    if (!recipe) return;

    document.getElementById('modalTitle').textContent = recipe.name || "Untitled";
    document.getElementById('modalCuisine').textContent = recipe.cuisine || "N/A";

    // Tags
    const tags = recipe.dietary_tags;
    document.getElementById('modalTags').textContent = (Array.isArray(tags) && tags.length) ? tags.join(", ") : "No tags";

    // Ingredients
    const ingList = document.getElementById('modalIngredients');
    ingList.innerHTML = '';
    const ingredients = recipe.ingredients || [];
    if (Array.isArray(ingredients)) {
        ingredients.forEach(ing => {
            const li = document.createElement('li');
            if (typeof ing === 'object' && ing !== null) {
                li.textContent = `${ing.name || 'Item'} ${ing.quantity ? '- ' + ing.quantity : ''}`;
            } else {
                li.textContent = String(ing);
            }
            ingList.appendChild(li);
        });
    } else {
        ingList.innerHTML = '<li>N/A</li>';
    }

    // Steps
    const stepsDiv = document.getElementById('modalSteps');
    const steps = recipe.cooking_steps;
    if (Array.isArray(steps) && steps.length) {
        stepsDiv.innerHTML = '<ol>' + steps.map(s => `<li>${s}</li>`).join('') + '</ol>';
    } else if (typeof steps === 'string') {
        stepsDiv.innerHTML = `<p>${steps}</p>`; // Basic text fallback
    } else {
        stepsDiv.innerHTML = '<p>N/A</p>';
    }

    document.getElementById('recipeModalOverlay').style.display = 'flex';
};

window.closeRecipeModal = function () {
    document.getElementById('recipeModalOverlay').style.display = 'none';
};

// Close on overlay click
document.getElementById('recipeModalOverlay').addEventListener('click', function (e) {
    if (e.target === this) window.closeRecipeModal();
});
// Close on Escape
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') window.closeRecipeModal();
});
