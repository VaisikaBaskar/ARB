// Make load function global so HTML can call it on init
window.loadPantryItems = function (userId) {
    if (!userId) userId = window.currentUserId;
    if (!userId) return;

    fetch(`http://localhost:5000/pantry/${userId}`)
        .then(response => response.json())
        .then(data => {
            const list = document.getElementById('pantryList');
            list.innerHTML = ""; // Clear existing

            if (data.length === 0) {
                list.innerHTML = "<li>No items found for this user.</li>";
                // Show empty state if possible (requires simple toggle logic)
                const emptyState = document.querySelector('.pantry-empty');
                if (emptyState) emptyState.style.display = 'block';
                return;
            } else {
                const emptyState = document.querySelector('.pantry-empty');
                if (emptyState) emptyState.style.display = 'none';
            }

            data.forEach(item => {
                const li = document.createElement('li');
                li.textContent = `${item.ingredient} - ${item.quantity || ''}`;

                // Add delete button
                const delBtn = document.createElement('button');
                delBtn.textContent = 'x';
                delBtn.style.marginLeft = '10px';
                delBtn.style.background = '#ffcccc';
                delBtn.style.color = 'red';
                delBtn.style.border = 'none';
                delBtn.style.padding = '2px 6px';
                delBtn.style.cursor = 'pointer';
                delBtn.onclick = () => deletePantryItem(userId, item.ingredient);
                li.appendChild(delBtn);

                list.appendChild(li);
            });
        })
        .catch(error => {
            console.error('Error fetching pantry:', error);
        });
};

function deletePantryItem(userId, ingredient) {
    fetch(`http://localhost:5000/pantry/${userId}/${ingredient}`, { method: 'DELETE' })
        .then(res => {
            if (res.ok) window.loadPantryItems(userId);
        });
}

document.getElementById('pantryForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const userId = window.currentUserId; // Use global authenticated ID
    const ingredient = document.getElementById('ingredient').value;
    const quantity = document.getElementById('quantity').value;

    if (!userId) {
        alert("Authentication error. Please re-login.");
        return;
    }

    const payload = {
        user_id: userId,
        ingredient: ingredient,
        quantity: quantity
    };

    fetch('http://localhost:5000/pantry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = data.message || "Item saved";
            messageDiv.style.color = "green";
            // Auto reload
            window.loadPantryItems(userId);
            document.getElementById('pantryForm').reset();
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('message').textContent = "Error saving item.";
        });
});

document.getElementById('loadPantry').addEventListener('click', function () {
    if (window.currentUserId) {
        window.loadPantryItems(window.currentUserId);
    }
});
