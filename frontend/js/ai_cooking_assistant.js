// frontend/js/ai_cooking_assistant.js
// Isolated UI Logic for AI Cooking Assistant

document.addEventListener('DOMContentLoaded', () => {
    const askBtn = document.querySelector('.ai-cook-btn');
    const inputField = document.querySelector('.ai-cook-textarea');
    const resultsContainer = document.querySelector('.ai-cook-results');

    if (askBtn && inputField && resultsContainer) {
        askBtn.addEventListener('click', async () => {
            const text = inputField.value.trim();
            if (!text) {
                alert("Please describe what you want to cook.");
                return;
            }

            // UI Loading State
            askBtn.disabled = true;
            askBtn.textContent = "Asking AI...";
            inputField.disabled = true;
            resultsContainer.innerHTML = '<p style="color: #666; text-align: center;">Thinking... 🤖</p>';

            // Get User ID safely
            const userId = window.currentUserId || localStorage.getItem('currentUserId') || null;

            try {
                const response = await fetch('http://localhost:5000/ai/cook', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text,
                        user_id: userId
                    })
                });

                const contentType = response.headers.get("content-type");
                let data;
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    data = await response.json();
                } else {
                    throw new Error("Invalid response from server");
                }

                if (data.success) {
                    renderResponse(data.data, resultsContainer);
                } else {
                    renderError(data.message || "AI could not process your request.", resultsContainer);
                }

            } catch (error) {
                console.error("AI Assistant Error:", error);
                renderError("Failed to connect to the kitchen. Please try again later.", resultsContainer);
            } finally {
                // Reset UI State
                askBtn.disabled = false;
                askBtn.textContent = "Ask AI";
                inputField.disabled = false;
                inputField.focus();
            }
        });
    }
});

function renderResponse(data, container) {
    // 1. Title
    let html = `<h2 style="color: #2c3e50; border-bottom: 2px solid #28a745; padding-bottom: 10px; margin-top: 0;">${data.title}</h2>`;

    // 2. Ingredients
    html += `<h3 style="color: #555; margin-bottom: 5px;">Ingredients needed:</h3>`;
    html += `<ul style="margin-top: 5px; color: #444;">`;
    data.ingredients.forEach(ing => {
        html += `<li>${ing}</li>`;
    });
    html += `</ul>`;

    // 3. Pantry Check (Optional)
    if (data.pantry) {
        // Available
        if (data.pantry.available && data.pantry.available.length > 0) {
            html += `<div style="background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 0.9em;">
                <strong>✅ You have:</strong> ${data.pantry.available.join(', ')}
            </div>`;
        }
        // Missing
        if (data.pantry.missing && data.pantry.missing.length > 0) {
            html += `<div style="background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 0.9em;">
                <strong>🛒 You might need:</strong> ${data.pantry.missing.join(', ')}
            </div>`;
        }
    }

    // 4. Steps
    html += `<h3 style="color: #555; margin-bottom: 5px; margin-top: 20px;">Cooking Instructions:</h3>`;
    html += `<div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #eee;">`;
    data.steps.forEach(step => {
        html += `<p style="margin: 8px 0; line-height: 1.5; color: #333;">${step}</p>`;
    });
    html += `</div>`;

    // 5. Save Button
    html += `<div style="margin-top: 30px; text-align: center;">
        <button id="save-ai-recipe-btn" style="background-color: #007bff; color: white; border: none; padding: 10px 25px; font-size: 1em; border-radius: 6px; cursor: pointer; transition: background 0.3s ease;">
            Save to My Recipes
        </button>
    </div>`;

    container.innerHTML = html;

    // Attach Event Listener (Isolated)
    const saveBtn = document.getElementById('save-ai-recipe-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => saveAiRecipe(data, saveBtn));
    }
}

async function saveAiRecipe(aiData, btn) {
    btn.disabled = true;
    btn.textContent = "Saving...";

    // Construct Recipe Object for Backend
    // aiData.ingredients is array of strings: "Rice: 200 g"
    // We need to pass them as-is or structured. The backend supports string ingredients.

    // Default Cuisine/Diet if not present
    // Since AI output is simplified, we set defaults
    const recipePayload = {
        name: aiData.title,
        ingredients: aiData.ingredients,
        cooking_steps: aiData.steps,
        cuisine: "AI Generated",
        dietary_tags: ["AI Chef"]
    };

    try {
        const userId = window.currentUserId || localStorage.getItem('currentUserId');

        // Add user_id to recipe if available (though backend might not enforce it for recipe doc itself if globally shared, 
        // usually recipes are just global or user specific? 
        // In this app, everyone sees all recipes? 
        // Based on app.py: recipes collection seems global. 
        // But let's send what we have.

        const response = await fetch('http://localhost:5000/ai/save-recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                recipe: recipePayload,
                user_id: userId // Optional context
            })
        });

        const result = await response.json();

        if (result.success) {
            btn.textContent = "Saved! ✅";
            btn.style.backgroundColor = "#28a745";
            setTimeout(() => {
                // Optional: Redirect or just leave it
                // btn.textContent = "Save to My Recipes";
                // btn.disabled = false;
            }, 2000);
        } else {
            btn.textContent = "Error Saving ❌";
            btn.style.backgroundColor = "#dc3545";
            setTimeout(() => {
                btn.textContent = "Save to My Recipes";
                btn.disabled = false;
                btn.style.backgroundColor = "#007bff";
            }, 3000);
            alert("Failed to save: " + result.message);
        }

    } catch (e) {
        console.error("Save Error:", e);
        btn.textContent = "Error ❌";
        btn.style.backgroundColor = "#dc3545";
        setTimeout(() => {
            btn.disabled = false;
            btn.textContent = "Save to My Recipes";
            btn.style.backgroundColor = "#007bff";
        }, 3000);
    }
}

function renderError(message, container) {
    container.innerHTML = `<div style="color: #dc3545; background: #ffe6e6; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ffcccc;">
        <strong>Error:</strong> ${message}
    </div>`;
}
