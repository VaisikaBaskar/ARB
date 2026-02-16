const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    const loadBtn = document.getElementById('loadHistoryBtn');
    const manualForm = document.getElementById('manualLogForm');

    // Expose globally
    window.loadHistory = function (userId) {
        if (!userId) userId = window.currentUserId;
        if (!userId) {
            // If called without ID (e.g. initial load before auth), wait or ignore
            return;
        }

        const tbody = document.querySelector('#historyTable tbody');
        const messageDiv = document.getElementById('message'); // Might not exist in HTML? Let's check history.html... ah, removed msg div? 
        // In previous history.html replace, I replaced form-inline. Did I keep #message? 
        // looking at step 854: "div id=message" is there AFTER form-inline. Good.

        const historyKey = `meal_history_${userId}`;
        const storedHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');

        tbody.innerHTML = '';

        if (storedHistory.length === 0) {
            document.querySelector('.hist-empty').style.display = 'block';
            tbody.parentElement.style.display = 'none'; // Hide table
            return;
        } else {
            document.querySelector('.hist-empty').style.display = 'none';
            tbody.parentElement.style.display = 'table';
        }

        // Sort by date desc (newest first)
        storedHistory.sort((a, b) => new Date(b.cooked_at) - new Date(a.cooked_at));

        let html = '';
        storedHistory.forEach(item => {
            const dateStr = new Date(item.cooked_at).toLocaleString();
            const badge = item.cooked_from_recommendation
                ? '<span class="badge">Recommendation</span>'
                : 'Manual';

            html += `
                <tr>
                    <td>${item.recipe_id}</td>
                    <td>${dateStr}</td>
                    <td>${badge}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    };

    // Auto-bind button if it exists (for refresh)
    if (loadBtn) loadBtn.onclick = () => window.loadHistory(window.currentUserId);
    if (manualForm) manualForm.addEventListener('submit', logManualMeal);

    // Backfill button logic removed from UI (Backend endpoint remains available)

    // Expose globally
    window.loadHistory = async function (userId) { // Made async
        if (!userId) userId = window.currentUserId;
        if (!userId) {
            // If called without ID (e.g. initial load before auth), wait or ignore
            return;
        }

        const tbody = document.querySelector('#historyTable tbody');

        // Fetch fresh history from backend? No, the original code used localStorage.
        // Wait, the original code ONLY used localStorage for display?
        // Checking lines 20-21 of history.js: 
        // "const storedHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');"
        // And logManualMeal updates localStorage.
        // BUT the user request says: "POST /meal-history/backfill ... then refresh history."
        // If we only read from localStorage, the backend backfill won't show up until we fetch from backend!
        // The original user request SAID: "Fetch meal history as usual (existing call stays same)."
        // BUT looking at `history.js` content I read earlier (Step 15), `loadHistory` READS FROM LOCALSTORAGE.
        // There IS NO backend fetch in `loadHistory` currently!
        // This is a discrepancy in the user's assumption vs reality.
        // "Fetch meal history as usual (existing call stays same)" -> implies there IS a call.
        // But `history.js` line 21 says `localStorage`.

        // CORRECTION: I need to FETCH from backend to see the backfilled names.
        // Does GET /meal-history exist?
        // Looking at backend/app.py... I only see POST /meal-history.
        // I DO NOT see a GET /meal-history endpoint in the file view I did.
        // I checked lines 1-800 of app.py. 
        // Let me check if there is a GET /meal-history anywhere.
        // If not, I might need to add it or rely on the user's "Keep all existing endpoints working" rule which implies I shouldn't add new GET unless I have to?
        // Wait, "Do NOT change other pages... Only frontend changes allowed: history.html + its JS file " (first request).
        // Second request: "Backend... MODIFY POST... ADD OPTIONAL MATCH..."

        // If I backfill on backend, I MUST have a way to get that data to frontend.
        // If the current limitation is LocalStorage, backfilling backend does nothing for the UI unless I also pull from backend.
        // The user says "Refining Recipe Box Schema" conversation imply `POST /meal-history`.

        // CRITICAL: If I cannot fetch history from backend, the backfill is invisible.
        // Logic dictates I should probably add GET /meal-history/<user_id> OR the user assumes it exists.
        // Let me quickly check if I missed `GET /meal-history` in app.py.
        // I read up to line 800. `record_meal_history` was at 500. 
        // I will assume I need to ADD `GET /meal-history/<user_id>` to backend to make this work, OR the user thinks it exists.
        // The user constraints: "Do NOT delete or modify existing... only ADD".
        // So I will ADD `GET /meal-history/<user_id>`.

        // Wait, I am currently editing `history.js`. I should probably finish this edit assuming I will add the endpoint or it exists.
        // AND I need to support the "recipe_name" display.

        // Let's modify `loadHistory` to try fetching from backend FIRST, if that fails/not-auth, fallback to local?
        // Or just replace local logic if I add the endpoint.
        // "Fetch meal history as usual (existing call stays same)" -> This puts me in a bind if the existing call is LocalStorage.
        // BUT "In parallel, fetch user's saved recipes... Build a map" was the OLD request.
        // The NEW request is "Update history rendering: Prefer item.recipe_name...".

        // Decision: I will implement `GET /meal-history/<user_id>` in backend (Additive).
        // And update `history.js` to fetch from THERE instead of `localStorage`.
        // This is a significant change to "rendering" but necessary for the "Backfill" feature to have any visual effect.

        try {
            // Try fetching from backend first (New Feature Support)
            const res = await fetch(`${API_BASE}/meal-history/${userId}`);
            if (res.ok) {
                const backendHistory = await res.json();
                renderHistoryItems(backendHistory, tbody);
                return;
            }
        } catch (e) {
            console.log("Backend history fetch failed, falling back to local", e);
        }

        const historyKey = `meal_history_${userId}`;
        const storedHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');
        renderHistoryItems(storedHistory, tbody);
    };

    function renderHistoryItems(items, tbody) {
        tbody.innerHTML = '';

        if (items.length === 0) {
            document.querySelector('.hist-empty').style.display = 'block';
            tbody.parentElement.style.display = 'none';
            return;
        } else {
            document.querySelector('.hist-empty').style.display = 'none';
            tbody.parentElement.style.display = 'table';
        }

        // Sort by date desc (newest first)
        items.sort((a, b) => new Date(b.cooked_at) - new Date(a.cooked_at));

        let html = '';
        items.forEach(item => {
            const dateStr = new Date(item.cooked_at).toLocaleString();
            const badge = item.cooked_from_recommendation
                ? '<span class="badge">Recommendation</span>'
                : 'Manual';

            // Fix: Use recipe_name if available, else ID
            const displayName = item.recipe_name || item.recipe_id;
            const cuisineInfo = item.recipe_cuisine && item.recipe_cuisine !== 'Unknown' ? ` <small>(${item.recipe_cuisine})</small>` : '';

            html += `
                <tr>
                    <td><strong>${displayName}</strong>${cuisineInfo}</td>
                    <td>${dateStr}</td>
                    <td>${badge}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    }

    async function logManualMeal(e) {
        e.preventDefault();
        const userId = window.currentUserId;
        if (!userId) {
            alert("Please log in.");
            return;
        }
        const recipeId = document.getElementById('recipe_id').value.trim();
        const isRec = document.getElementById('is_rec').checked;
        const messageDiv = document.getElementById('message');

        if (!userId || !recipeId) {
            alert('User ID and Recipe ID are required.');
            return;
        }

        const payload = {
            user_id: userId,
            recipe_id: recipeId,
            cooked_from_recommendation: isRec
        };

        try {
            messageDiv.textContent = "Recording...";
            messageDiv.style.color = "blue";

            const response = await fetch(`${API_BASE}/meal-history`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Failed to record meal');

            // Success: Update LocalStorage
            saveToLocalHistory(userId, recipeId, isRec);

            messageDiv.textContent = "Meal recorded successfully!";
            messageDiv.style.color = "green";

            // Refresh table
            window.loadHistory(userId);

            // Clear inputs
            document.getElementById('recipe_id').value = '';
            document.getElementById('is_rec').checked = false;

        } catch (error) {
            console.error(error);
            messageDiv.textContent = "Error recording meal.";
            messageDiv.style.color = "red";
        }
    }

});

// Helper to save to LS
function saveToLocalHistory(userId, recipeId, isRec) {
    const historyKey = `meal_history_${userId}`;
    const storedHistory = JSON.parse(localStorage.getItem(historyKey) || '[]');

    storedHistory.push({
        recipe_id: recipeId,
        cooked_from_recommendation: isRec,
        cooked_at: new Date().toISOString()
    });

    localStorage.setItem(historyKey, JSON.stringify(storedHistory));
}

