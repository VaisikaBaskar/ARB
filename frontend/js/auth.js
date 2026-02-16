// Authentication Logic

// Check if user is logged in
function checkAuth(shouldRedirect = true) {
    if (localStorage.getItem("loggingOut") === "true") {
        localStorage.removeItem("loggingOut"); // Cleanup
        return;
    }
    return fetch('/auth/me', { credentials: 'include' })
        .then(response => response.json())
        .then(data => {
            if (data.user_id) {
                console.log("Logged in as:", data.user_id);
                if (window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('signup.html')) {
                    window.location.href = 'index.html';
                }
                injectUserId(data.user_id);
                window.currentUserId = data.user_id; // Global access
                return data.user_id;
            } else {
                console.log("Not logged in");
                window.currentUserId = null;
                // Only redirect if NOT on login/signup pages
                const isAuthPage = window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('signup.html');
                if (shouldRedirect && !isAuthPage) {
                    window.location.href = 'login.html';
                }
                return null;
            }
        })
        .catch(err => console.error("Auth check failed", err));
}

// Inject user_id into forms if not index.html (which has manual entry removed or hidden typically, or prefilled)
function injectUserId(userId) {
    const input = document.getElementById('user_id');
    if (input) {
        input.value = userId;
        // Make it read-only so they don't accidentally edit it and save to wrong user
        input.setAttribute('readonly', true);
    }
    // Update any UI elements showing ID
    const display = document.getElementById('user-display');
    if (display) {
        display.textContent = `Logged in as: ${userId}`;
        display.style.display = 'block';
    }
}

// Login Function
function login(userId, password) {
    fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId.trim(), password: password.trim() }),
        credentials: 'include'
    })
        .then(res => res.json().then(data => ({ status: res.status, body: data })))
        .then(result => {
            if (result.status === 200) {
                window.location.href = 'index.html';
            } else {
                alert(result.body.error || "Login failed");
            }
        })
        .catch(err => alert("Login error"));
}

// Signup Function
function signup(userId, password) {
    fetch('/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId.trim(), password: password.trim() }),
        credentials: 'include'
    })
        .then(res => res.json().then(data => ({ status: res.status, body: data })))
        .then(result => {
            if (result.status === 201) {
                alert("Account created! Please log in.");
                window.location.href = 'login.html';
            } else {
                alert(result.body.error || "Signup failed");
            }
        })
        .catch(err => alert("Signup error"));
}

// Logout Function
function logoutUser() {
    localStorage.setItem("loggingOut", "true");
    return fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
    })
        .then(() => {
            window.location.replace('login.html');
        })
        .catch(err => {
            console.error("Logout failed", err);
            window.location.replace('login.html'); // Fallback
        });
}
