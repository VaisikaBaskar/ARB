const API_BASE = 'http://localhost:5000';

document.addEventListener('DOMContentLoaded', () => {
    // === ELEMENTS ===
    const editProfileBtn = document.getElementById('editProfileBtn');
    const profileModal = document.getElementById('profileModal');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const loadBtn = document.getElementById('loadBtn');
    const messageDiv = document.getElementById('message');

    // === INIT ===
    init();

    function init() {
        // Auto-load Priority:
        // 1. window.currentUserId (from auth.js if already set)
        // 2. Session (via API 401 check)
        // 3. Fallback ('user1')

        // Remove Load Button logic (UI removed)

        attemptAutoLoad();

        editProfileBtn.addEventListener('click', openEditModal);
        cancelEditBtn.addEventListener('click', closeEditModal);
        saveAllBtn.addEventListener('click', saveUnifiedProfile);
    }

    async function attemptAutoLoad() {
        // 1. Try generic load (backend checks session)
        // Pass nothing initially
        let uid = window.currentUserId || localStorage.getItem('user_id'); // If auth.js ran fast

        if (uid) {
            document.getElementById('user_id').value = uid;
            await loadUnifiedProfile(uid);
        } else {
            // Try session via API
            await loadUnifiedProfile(null);
        }
    }

    // ==========================================
    //           UNIFIED PROFILE LOGIC
    // ==========================================
    // Global state to hold current data for pre-filling modal
    let currentProfileData = null;

    async function loadUnifiedProfile(userId) {
        try {
            showMessage('Loading...', 'blue');

            let url = `${API_BASE}/api/profile`;
            if (userId) {
                url += `?user_id=${userId}`;
            }

            // Fetch with credentials (session cookie)
            const response = await fetch(url, { credentials: 'include' });

            if (response.status === 401) {
                // Fallback Logic
                if (!userId) {
                    // We tried session, failed. Try fallback 'user1'
                    console.log("Session load failed, trying fallback: user1");
                    return loadUnifiedProfile('user1');
                } else {
                    showMessage('Unauthorized. Please log in.', 'red');
                    return;
                }
            }

            const data = await response.json();

            // Store globally for Edit Modal
            currentProfileData = data.profile;

            // Important: Update hidden input if we loaded from session or fallback
            if (data.profile && data.profile.user_id) {
                document.getElementById('user_id').value = data.profile.user_id;
                window.currentUserId = data.profile.user_id; // Sync global
                // Also update localStorage if auth uses it? Auth.js handles that usually.
            }

            if (data.exists || data.profile) {
                renderProfileView(data.profile);
                showMessage('');
            } else {
                renderProfileView(data.profile, true); // Empty state
                showMessage('New user profile ready.', 'green');
            }
        } catch (error) {
            console.error("Load Error:", error);
            showMessage('Error loading profile.', 'red');
        }
    }

    function renderProfileView(profile, isEmpty = false) {
        // 1. Social Card
        document.getElementById('display_name').textContent = profile.full_name || "New User";
        document.getElementById('display_username').textContent = profile.username ? `@${profile.username}` : "@user";
        document.getElementById('display_bio').textContent = profile.bio || "No bio yet.";
        document.getElementById('display_avatar').src = profile.avatar_url || "https://ui-avatars.com/api/?name=" + (profile.full_name || "User");

        // 2. Preferences View
        const prefs = profile.preferences || {};
        document.getElementById('view_diet').textContent = prefs.diet || "Not set";

        const cuisines = (prefs.favorite_cuisines && prefs.favorite_cuisines.length > 0) ? prefs.favorite_cuisines.join(", ") : "Not set";
        document.getElementById('view_cuisines').textContent = cuisines;

        const tags = (prefs.dietary_tags && prefs.dietary_tags.length > 0) ? prefs.dietary_tags.join(", ") : "Not set";
        document.getElementById('view_tags').textContent = tags;

        // Handle string or array for ingredients
        let likedList = prefs.liked_ingredients || [];
        if (typeof likedList === 'string') likedList = [likedList];
        document.getElementById('view_liked').textContent = likedList.length ? likedList.join(", ") : "Not set";

        let dislikedList = prefs.disliked_ingredients || [];
        if (typeof dislikedList === 'string') dislikedList = [dislikedList];
        document.getElementById('view_disliked').textContent = dislikedList.length ? dislikedList.join(", ") : "Not set";
    }

    function openEditModal() {
        const userId = document.getElementById('user_id').value.trim();
        if (!userId) return alert("Please load a user first");

        // Pre-fill inputs from currentProfileData
        const p = currentProfileData || {};
        const prefs = p.preferences || {};

        // Social
        document.getElementById('edit_fullname').value = p.full_name || "";
        document.getElementById('edit_username').value = p.username || "";
        document.getElementById('edit_bio').value = p.bio || "";
        document.getElementById('edit_avatar').value = p.avatar_url || "";

        // Preferences
        document.getElementById('edit_diet').value = prefs.diet || "";

        setCheckedValues('edit_cuisine', prefs.favorite_cuisines || []);
        setCheckedValues('edit_tag', prefs.dietary_tags || []);

        // Ingredients input (Array -> Comma String)
        let likedStr = prefs.liked_ingredients || [];
        if (Array.isArray(likedStr)) likedStr = likedStr.join(", ");
        document.getElementById('edit_liked').value = likedStr;

        let dislikedStr = prefs.disliked_ingredients || [];
        if (Array.isArray(dislikedStr)) dislikedStr = dislikedStr.join(", ");
        document.getElementById('edit_disliked').value = dislikedStr;

        profileModal.style.display = 'block';
    }

    function closeEditModal() {
        profileModal.style.display = 'none';
    }

    async function saveUnifiedProfile() {
        const userId = document.getElementById('user_id').value.trim();

        // Collect Preferences
        const diet = document.getElementById('edit_diet').value;
        const favoriteCuisines = getCheckedValues('edit_cuisine');
        const dietaryTags = getCheckedValues('edit_tag');
        const likedIngredients = parseCommaSeparated(document.getElementById('edit_liked').value);
        const dislikedIngredients = parseCommaSeparated(document.getElementById('edit_disliked').value);

        const payload = {
            user_id: userId,
            // Social
            full_name: document.getElementById('edit_fullname').value,
            username: document.getElementById('edit_username').value,
            bio: document.getElementById('edit_bio').value,
            avatar_url: document.getElementById('edit_avatar').value,
            // Nested Preferences
            preferences: {
                diet: diet,
                favorite_cuisines: favoriteCuisines,
                dietary_tags: dietaryTags,
                liked_ingredients: likedIngredients,
                disliked_ingredients: dislikedIngredients
            }
        };

        try {
            showMessage('Saving...', 'blue');

            // Always PUT (Upsert logic in backend)
            const response = await fetch(`${API_BASE}/api/profile`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const data = await response.json();
                // Update local state and view
                currentProfileData = data.profile;
                renderProfileView(data.profile);
                closeEditModal();
                showMessage('Profile updated successfully!', 'green');
            } else {
                throw new Error("Failed to save");
            }

        } catch (e) {
            console.error(e);
            showMessage('Error saving profile.', 'red');
        }
    }

    // Helpers
    function getCheckedValues(nameValue) {
        const checkboxes = document.querySelectorAll(`input[name="${nameValue}"]:checked`);
        return Array.from(checkboxes).map(cb => cb.value);
    }

    function setCheckedValues(nameValue, values) {
        document.querySelectorAll(`input[name="${nameValue}"]`).forEach(cb => cb.checked = false);
        values.forEach(val => {
            const cb = document.querySelector(`input[name="${nameValue}"][value="${val}"]`);
            if (cb) cb.checked = true;
        });
    }

    function parseCommaSeparated(str) {
        return str.split(',').map(s => s.trim()).filter(s => s.length > 0);
    }

    function showMessage(msg, color) {
        messageDiv.textContent = msg;
        messageDiv.style.color = color || 'black';
    }
});
