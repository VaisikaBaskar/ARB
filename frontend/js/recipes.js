document.getElementById('recipeForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const recipeId = document.getElementById('recipe_id').value;
    constname = document.getElementById('name').value;
    const ingredientsRaw = document.getElementById('ingredients').value;
    const diet = document.getElementById('diet').value;
    const cuisine = document.getElementById('cuisine').value;
    const cookTime = document.getElementById('cook_time').value;

    // Convert comma-separated string to list
    const ingredients = ingredientsRaw.split(',').map(item => item.trim()).filter(item => item !== "");

    const payload = {
        recipe_id: recipeId,
        name: name, // Note: element id 'name' might conflict if not careful, but .value is fine
        ingredients: ingredients,
        diet: diet,
        cuisine: cuisine,
        cook_time: parseInt(cookTime) || 0
    };

    fetch('http://localhost:5000/recipe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = data.message || "Operation completed";
            messageDiv.style.color = "green";
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('message').textContent = "Error saving recipe.";
            document.getElementById('message').style.color = "red";
        });
});
