window.getRecommendations = function (userId) {
    if (!userId) userId = window.currentUserId;
    if (!userId) {
        // Warning if no user
        return;
    }

    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<p>Loading recommendations...</p>';

    // Hide empty state initially
    const emptyState = document.querySelector('.rec-empty');
    if (emptyState) emptyState.style.display = 'none';

    fetch(`http://localhost:5000/recommend/${userId}`)
        .then(res => res.json())
        .then(data => {
            resultsDiv.innerHTML = '';

            if (data.length === 0) {
                if (emptyState) emptyState.style.display = 'block';
                resultsDiv.innerHTML = '<p></p>'; // Clear loading text
                return;
            }

            const ul = document.createElement('ul');
            data.forEach(recipe => {
                const li = document.createElement('li');
                li.style.marginBottom = "15px";
                li.style.padding = "10px";
                li.style.border = "1px solid #eee";

                const explanations = [];

                // 1. Pantry Match
                if (recipe.missing_count === 0) {
                    explanations.push('<span class="icon-check">✔</span> Full Pantry Match (You have all items)');
                } else {
                    explanations.push(`<span class="icon-info">ℹ</span> Missing ${recipe.missing_count} ingredient(s)`);
                }

                // 2. Score
                explanations.push(`<span class="icon-check">✔</span> High Relevance Score (${recipe.match_score.toFixed(1)})`);

                // 3. Recency
                if (recipe.recently_cooked) {
                    explanations.push('<span class="icon-warn">⚠</span> You cooked this recently (Lower priority)');
                } else {
                    explanations.push('<span class="icon-check">✔</span> Not cooked recently (Variety boost)');
                }

                // 4. Fallback for Preference fields (Cuisine, Tags) - implicitly handled by score but listed if data exists
                if (recipe.cuisine) {
                    explanations.push(`<span class="icon-check">✔</span> Matches cuisine preference: ${recipe.cuisine}`);
                }

                const explanationHtml = explanations.map(e => `<div class="explanation-item">${e}</div>`).join('');

                li.innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr auto auto; gap: 20px; align-items: center;">
                        
                        <!-- LEFT: Recipe Info -->
                        <div class="recipe-left" style="display:flex; flex-direction:column; align-items:flex-start; gap: 5px;">
                            <div style="display:flex; align-items:center; gap: 8px; flex-wrap: wrap;">
                                <strong style="font-size:1.15em; color: #333;">${recipe.name}</strong>
                                ${recipe.source === 'ai' ? '<span style="background:#e3f2fd; color:#0d47a1; font-size:0.75em; padding:2px 6px; border-radius:4px; border:1px solid #bbdefb; font-weight:600;">🤖 AI Suggested</span>' : ''}
                            </div>
                            
                            <button class="explanation-toggle" onclick="toggleExplanation('expl_${recipe.recipe_id}')" style="background:none; border:none; color:#007bff; padding:0; cursor:pointer; font-size:0.9em; text-decoration:none; border-bottom: 1px dashed #007bff;">
                                Why this recipe?
                            </button>
                            
                            <div id="expl_${recipe.recipe_id}" class="explanation-box" style="display:none; margin-top:10px; padding:10px; background:#f9f9f9; border-left:4px solid #007bff; border-radius:4px; width: 100%; box-sizing: border-box;">
                                <strong style="font-size:0.9em; color:#444; display:block; margin-bottom:5px;">Why we recommended this:</strong>
                                <div style="font-size:0.9em; line-height:1.5; color:#555;">${explanationHtml}</div>
                            </div>
                        </div>

                        <!-- CENTER: Badge -->
                        <div class="recipe-center" style="display:flex; justify-content:center; padding: 0 10px;">
                            <span style="background:#e8f5e9; color:#2e7d32; padding:6px 12px; border-radius:20px; font-size:0.95em; font-weight:700; white-space:nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                                ${recipe.match_score.toFixed(0)}% Match
                            </span>
                        </div>

                        <!-- RIGHT: Actions -->
                        <div class="recipe-right" style="display:flex; flex-direction:column; align-items:flex-end; gap: 10px;">
                            <label style="font-size:0.9em; cursor:pointer; display:flex; align-items:center; gap:8px; color:#555; background: #f8f9fa; padding: 4px 8px; border-radius: 4px;">
                                <input type="checkbox" id="cb_${recipe.recipe_id}" checked style="accent-color:#28a745; width: 16px; height: 16px;"> 
                                From Rec?
                            </label>
                            <button onclick="markAsCooked('${recipe.recipe_id}', '${userId}')" style="font-size:0.9em; padding:8px 16px; background-color:#28a745; color:white; border:none; border-radius:6px; cursor:pointer; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                Mark as Cooked
                            </button>
                        </div>

                    </div>
                `;
                ul.appendChild(li);
            });
            resultsDiv.appendChild(ul);
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = "<p style='text-align:center; color:red;'>Error fetching recommendations.</p>";
        });
};

function toggleExplanation(id) {
    const el = document.getElementById(id);
    if (el.style.display === 'block') {
        el.style.display = 'none';
    } else {
        el.style.display = 'block';
    }
}

// Function to handle "Mark as Cooked"
async function markAsCooked(recipeId, userId) {
    const isRec = document.getElementById(`cb_${recipeId}`).checked;

    // Optimistic UI feedback
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = "Saving...";
    btn.disabled = true;

    try {
        const response = await fetch(`http://localhost:5000/meal-history`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                recipe_id: recipeId,
                cooked_from_recommendation: isRec
            })
        });

        if (response.ok) {
            btn.textContent = "Cooked!";
            btn.style.backgroundColor = "green";

            // Save to LocalStorage for History Page
            const historyKey = `meal_history_${userId}`;
            const storedHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');
            storedHistory.push({
                recipe_id: recipeId,
                cooked_from_recommendation: isRec,
                cooked_at: new Date().toISOString()
            });
            localStorage.setItem(historyKey, JSON.stringify(storedHistory));

        } else {
            throw new Error("Failed");
        }
    } catch (e) {
        console.error(e);
        btn.textContent = "Error";
        btn.style.backgroundColor = "red";
        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
            btn.style.backgroundColor = ""; // reset
        }, 2000);
    }
}

// Refresh logic
function refreshRecommendations() {
    const userId = window.currentUserId;
    if (userId && typeof window.getRecommendations === 'function') {
        window.getRecommendations(userId);
    } else {
        console.warn("User ID not found or getRecommendations not ready.");
        // Attempt re-auth if needed, or just let user navigate
        checkAuth(true);
    }
}

// Bind event listener when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshRecommendations);
    }
});

// Also expose globally just in case
window.refreshRecommendations = refreshRecommendations;
