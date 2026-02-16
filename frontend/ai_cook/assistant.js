// AI Cooking Assistant - Isolated Logic
// No dependencies on main app.js or global auth

document.addEventListener('DOMContentLoaded', () => {
    // Input Handling
    const askBtn = document.getElementById('askAiBtn');
    const inputField = document.getElementById('aiInput');
    const responseBox = document.getElementById('aiResponse');
    const responseText = document.getElementById('responseText');

    if (askBtn && inputField) {
        askBtn.addEventListener('click', () => {
            const query = inputField.value.trim();
            if (!query) {
                alert("Please describe what you want to cook first.");
                return;
            }

            // Simulate Processing
            askBtn.disabled = true;
            askBtn.textContent = "Analysing...";
            askBtn.style.opacity = "0.7";

            // Simple client-side echo (Stateless)
            setTimeout(() => {
                responseBox.style.display = 'block';
                responseText.textContent = `Received Input: "${query}"\n\n[System]: Backend integration is currently pending next phase. This input would be sent to the LLM agent.`;

                // Reset UI
                askBtn.disabled = false;
                askBtn.textContent = "Ask AI";
                askBtn.style.opacity = "1";
            }, 800);
        });
    }

    // Status Check (Previous Logic - kept for continuity)
    const btn = document.getElementById('checkStatusBtn');
    const output = document.getElementById('statusOutput');

    if (btn) {
        btn.addEventListener('click', async () => {
            output.textContent = "Checking...";
            try {
                const res = await fetch('http://localhost:5000/ai-cook/status');
                if (res.ok) {
                    const data = await res.json();
                    output.textContent = `✅ ${data.message}`;
                    output.style.color = "green";
                } else {
                    output.textContent = "⚠️ Module not registered (Expected Behavior)";
                    output.style.color = "orange";
                }
            } catch (e) {
                output.textContent = "🔒 Feature is safely isolated (Network Unreachable)";
                output.style.color = "#555";
            }
        });
    }
});
