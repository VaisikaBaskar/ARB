document.addEventListener('DOMContentLoaded', () => {
    // 1. Guard: Ensure only one nav exists
    if (document.getElementById('universal-nav')) return;

    // 2. Navigation Logic (Smart Next)
    const currentPath = window.location.pathname;

    // Store current path in stack if needed, but for now we focus on "next hint"
    // We update "last_page" just in case we need it, but browser back handles "Back" well.
    sessionStorage.setItem('nav_last_page', currentPath);

    // 3. Inject Header
    const header = document.createElement('header');
    header.id = 'universal-nav';
    header.className = 'app-nav';

    // Determine Next Target
    // Rule: If nav_next_hint exists and is NOT current page, use it. Else default to Dashboard.
    let nextTarget = sessionStorage.getItem('nav_next_hint');
    if (!nextTarget || nextTarget === currentPath) {
        nextTarget = '/'; // Default to Dashboard/Home
    }

    header.innerHTML = `
        <div class="nav-left">
            <button class="nav-btn back-btn" onclick="window.history.back()">
                &larr; Back
            </button>
        </div>
        
        <nav class="nav-center">
            <a href="/" class="nav-link" data-path="/">Home</a>
            <a href="recipes.html" class="nav-link" data-path="/recipes.html">Recipes</a>
            <a href="pantry.html" class="nav-link" data-path="/pantry.html">Pantry</a>
            <a href="recommend.html" class="nav-link" data-path="/recommend.html">Recommend</a>
            <a href="history.html" class="nav-link" data-path="/history.html">History</a>
            <a href="profile.html" class="nav-link" data-path="/profile.html">Profile</a>
        </nav>

        <div class="nav-right">
            <a href="${nextTarget}" class="nav-btn next-btn">
                Next &rarr;
            </a>
        </div>
    `;

    // Inject Header
    document.body.insertAdjacentElement('afterbegin', header);

    // Inject Spacer (Safe layout push-down without modifying body padding)
    const spacer = document.createElement('div');
    spacer.id = 'nav-spacer';
    spacer.style.height = '56px'; // Matches header height
    spacer.style.width = '100%';
    spacer.style.display = 'block'; // Ensure it takes space
    header.insertAdjacentElement('afterend', spacer);

    // 4. Highlight Active Link & Attach Click Listeners
    const links = header.querySelectorAll('.nav-link');
    links.forEach(link => {
        const linkPath = link.getAttribute('data-path');

        // Highlight logic
        if (currentPath === linkPath ||
            (currentPath === '/index.html' && linkPath === '/') ||
            (currentPath === '/' && linkPath === '/')) {
            link.classList.add('active');
        }

        // Smart Next Logic: clicking a link sets it as the "next hint"
        // This means "I am interested in this flow"
        link.addEventListener('click', () => {
            sessionStorage.setItem('nav_next_hint', linkPath);
        });
    });

    // Also attach listener to Next button to clear hint if we reach it? 
    // Or keep it persistent? Prompt implies persistent flow intention.
    // Safety Guard: Remove Legacy Nav if detected
    // Legacy signature: "Home" + "Recs" + "Pantry" (Sidebar uses "Manage Pantry" and "Recommendations", no "Home")
    const legacyCandidates = document.querySelectorAll('nav:not(.app-nav)');
    legacyCandidates.forEach(nav => {
        const text = nav.innerText;
        if (text.includes('Home') && text.includes('Recs') && text.includes('Pantry')) {
            nav.remove();
            console.log('Legacy nav removed by Safety Guard');
        }
    });
});
