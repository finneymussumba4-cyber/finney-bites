const API = "";

let products = [];
let categories = [];
let deliveryZones = [];
let cart = [];
let selectedCategory = null;

const money = amount =>
    new Intl.NumberFormat("en-KE", {
        maximumFractionDigits: 0
    }).format(amount);

async function fetchData(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error("Unable to load data.");
    }

    return response.json();
}

// LOAD CATEGORIES
async function loadCategories() {
    const container = document.getElementById("categoriesContainer");

    try {
        categories = await fetchData("/api/categories/");

        container.innerHTML = "";

        const allButton = document.createElement("button");
        allButton.className = "category-card active";
        allButton.textContent = "All Foods";

        allButton.addEventListener("click", () => {
            selectedCategory = null;
            updateCategoryButtons(allButton);
            displayProducts();
        });

        container.appendChild(allButton);

        categories.forEach(category => {
            const button = document.createElement("button");

            button.className = "category-card";
            button.textContent = category.name;

            button.addEventListener("click", () => {
                selectedCategory = category.id;
                updateCategoryButtons(button);
                displayProducts();
            });

            container.appendChild(button);
        });

    } catch (error) {
        container.textContent = "Unable to load food categories.";
        console.error(error);
    }
}

function updateCategoryButtons(activeButton) {
    document.querySelectorAll(".category-card").forEach(button => {
        button.classList.remove("active");
    });

    activeButton.classList.add("active");
}

// LOAD PRODUCTS
async function loadProducts() {
    const container = document.getElementById("productsContainer");

    try {
        products = await fetchData("/api/products/");
        displayProducts();

    } catch (error) {
        container.textContent = "Unable to load our menu.";
        console.error(error);
    }
}

// DISPLAY PRODUCTS
function displayProducts() {
    const container = document.getElementById("productsContainer");
    const search = document.getElementById("searchInput").value.toLowerCase();

    container.innerHTML = "";

    const filtered = products.filter(product => {
        const matchesCategory =
            selectedCategory === null ||
            product.category_id === selectedCategory;

        const matchesSearch =
            product.name.toLowerCase().includes(search);

        return matchesCategory && matchesSearch;
    });

    if (filtered.length === 0) {
        container.textContent = "No food items found.";
        return;
    }

    filtered.forEach(product => {
        const card = document.createElement("article");
        card.className = "product-card";

        const image = document.createElement("div");
        image.className = "product-image";

        if (product.image) {
            const img = document.createElement("img");
            img.src = product.image;
            img.alt = product.name;
            img.style.width = "100%";
            img.style.height = "100%";
            img.style.objectFit = "contain";

            img.onerror = () => {
                image.textContent = "??";
            };

            image.appendChild(img);
        } else {
            image.textContent = "??";
        }

        const info = document.createElement("div");
        info.className = "product-info";

        const name = document.createElement("h3");
        name.textContent = product.name;

        const description = document.createElement("p");
        description.className = "product-description";
        description.textContent = product.description || "Delicious food from FINNEY BITES.";

        const price = document.createElement("p");
        price.className = "product-price";
        price.textContent = "KSh " + money(Number(product.price));

        const button = document.createElement("button");

        const available =
            product.is_available && product.stock_quantity > 0;

        button.textContent = available ? "Add to Cart" : "Out of Stock";
        button.disabled = !available;

        if (!available) {
            button.style.opacity = "0.5";
            button.style.cursor = "not-allowed";
        }

        button.addEventListener("click", () => {
            addToCart(product.id);
        });

        const favoriteButton = document.createElement("button");
        favoriteButton.textContent = "? Save to Favourites";
        favoriteButton.className = "favorite-button";

        favoriteButton.addEventListener("click", async () => {
            if (!currentCustomer) {
                accountModal.hidden = false;
                document.getElementById("accountMessage").textContent =
                    "Please sign in to save your favourite meals.";
                return;
            }

            try {
                await accountRequest(
                    `/api/customer/favorites/${product.id}`,
                    { method: "POST" }
                );

                favoriteButton.textContent = "? Saved";
            } catch (error) {
                alert(error.message);
            }
        });

        button.className = "add-to-cart-button";

        const ingredientsButton = document.createElement("button");
        ingredientsButton.textContent = "Ingredients";
        ingredientsButton.className = "ingredients-button";

        ingredientsButton.addEventListener("click", () => {
            const details = window.PRODUCT_INGREDIENTS?.[product.id];

            if (!details) {
                alert("Ingredient information is not available yet.");
                return;
            }

            const overlay = document.createElement("div");
            overlay.style.cssText = "position:fixed;inset:0;background:#0009;z-index:99999;display:flex;align-items:center;justify-content:center;padding:15px;";

            const popup = document.createElement("div");
            popup.style.cssText = "background:white;padding:25px;border-radius:15px;width:100%;max-width:450px;max-height:85vh;overflow-y:auto;color:#292929;";

            const title = document.createElement("h2");
            title.textContent = product.name;

            const priceText = document.createElement("p");
            priceText.textContent = "Price: KSh " + money(Number(product.price));

            const servingTitle = document.createElement("h3");
            servingTitle.textContent = "Serving Quantity";

            const serving = document.createElement("p");
            serving.textContent = details.serving;

            const ingredientsTitle = document.createElement("h3");
            ingredientsTitle.textContent = "Ingredients";

            const ingredients = document.createElement("p");
            ingredients.textContent = details.ingredients;

            const preparationTitle = document.createElement("h3");
            preparationTitle.textContent = "Preparation";

            const preparation = document.createElement("p");
            preparation.textContent = details.preparation;

            const close = document.createElement("button");
            close.textContent = "Close";
            close.style.cssText = "background:#ff7518;color:white;border:0;padding:10px 25px;border-radius:8px;cursor:pointer;";
            close.addEventListener("click", () => overlay.remove());

            popup.append(title, priceText, servingTitle, serving, ingredientsTitle, ingredients, preparationTitle, preparation, close);
            overlay.appendChild(popup);
            overlay.addEventListener("click", event => {
                if (event.target === overlay) overlay.remove();
            });

            document.body.appendChild(overlay);
        });

        const actionRow = document.createElement("div");
        actionRow.className = "product-action-row";
        actionRow.append(favoriteButton, ingredientsButton);

        info.append(name, description, price, button, actionRow);
        card.append(image, info);
        container.appendChild(card);
    });
}

// SHOPPING CART
function addToCart(productId) {
    const product = products.find(item => item.id === productId);

    if (!product || !product.is_available) return;

    const existing = cart.find(item => item.product_id === productId);

    if (existing) {
        if (existing.quantity >= product.stock_quantity) {
            alert("Sorry, available stock has been reached.");
            return;
        }

        existing.quantity++;
    } else {
        cart.push({
            product_id: productId,
            quantity: 1
        });
    }

    displayCart();
}

function changeQuantity(productId, amount) {
    const item = cart.find(item => item.product_id === productId);
    const product = products.find(item => item.id === productId);

    if (!item || !product) return;

    const newQuantity = item.quantity + amount;

    if (newQuantity <= 0) {
        cart = cart.filter(item => item.product_id !== productId);
    } else if (newQuantity <= product.stock_quantity) {
        item.quantity = newQuantity;
    } else {
        alert("Sorry, available stock has been reached.");
    }

    displayCart();
}

function displayCart() {
    const container = document.getElementById("cartItems");

    container.innerHTML = "";

    let total = 0;
    let count = 0;

    if (cart.length === 0) {
        container.textContent = "Your cart is currently empty.";
    }

    cart.forEach(item => {
        const product = products.find(
            product => product.id === item.product_id
        );

        if (!product) return;

        const lineTotal = Number(product.price) * item.quantity;

        total += lineTotal;
        count += item.quantity;

        const row = document.createElement("div");
        row.className = "cart-item";

        const details = document.createElement("span");
        details.textContent =
            `${product.name} - KSh ${money(lineTotal)}`;

        const controls = document.createElement("div");

        const decrease = document.createElement("button");
        decrease.textContent = "-";
        decrease.addEventListener("click", () => {
            changeQuantity(product.id, -1);
        });

        const quantity = document.createElement("span");
        quantity.textContent = ` ${item.quantity} `;

        const increase = document.createElement("button");
        increase.textContent = "+";
        increase.addEventListener("click", () => {
            changeQuantity(product.id, 1);
        });

        controls.append(decrease, quantity, increase);
        row.append(details, controls);

        container.appendChild(row);
    });

    document.getElementById("cartTotal").textContent = money(total);
    document.getElementById("cartCount").textContent = count;
}

// LOAD DELIVERY ZONES
async function loadDeliveryZones() {
    const select = document.getElementById("deliveryZone");

    try {
        deliveryZones = await fetchData("/api/orders/delivery-zones");

        deliveryZones.forEach(zone => {
            const option = document.createElement("option");

            option.value = zone.id;
            option.textContent =
                `${zone.name} - KSh ${money(zone.delivery_fee)}`;

            select.appendChild(option);
        });

    } catch (error) {
        console.error(error);
        document.getElementById("orderMessage").textContent =
            "Unable to load delivery areas.";
    }
}

// ORDER TYPE
document.getElementById("orderType").addEventListener("change", event => {
    const delivery = event.target.value === "delivery";
    const fields = document.getElementById("deliveryFields");

    fields.hidden = !delivery;

    document.getElementById("deliveryZone").required = delivery;
    document.getElementById("deliveryAddress").required = delivery;
});

// SEARCH
document.getElementById("searchInput").addEventListener("input", () => {
    displayProducts();
});

// CART BUTTON
document.getElementById("cartButton").addEventListener("click", () => {
    document.getElementById("cart").scrollIntoView({
        behavior: "smooth"
    });
});

// CHECKOUT BUTTON
document.getElementById("checkoutButton").addEventListener("click", () => {
    if (cart.length === 0) {
        alert("Please add food to your cart first.");
        return;
    }

    document.getElementById("checkout").scrollIntoView({
        behavior: "smooth"
    });
});

// PLACE ORDER
document.getElementById("checkoutForm").addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("orderMessage");

    if (cart.length === 0) {
        message.textContent = "Your cart is empty.";
        return;
    }

    const orderType = document.getElementById("orderType").value;

    const orderData = {
        customer_name: document.getElementById("customerName").value.trim(),
        customer_phone: document.getElementById("customerPhone").value.trim(),
        customer_email: document.getElementById("customerEmail").value.trim() || null,
        order_type: orderType,
        delivery_zone_id: orderType === "delivery"
            ? Number(document.getElementById("deliveryZone").value)
            : null,
        delivery_address: orderType === "delivery"
            ? document.getElementById("deliveryAddress").value.trim()
            : null,
        notes: document.getElementById("orderNotes").value.trim() || null,
        items: cart.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity
        }))
    };

    const submitButton = event.submitter;
    submitButton.disabled = true;
    submitButton.textContent = "Processing...";

    message.textContent = "Submitting your order...";

    try {
        const response = await fetch("/api/orders/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof result.detail === "string"
                    ? result.detail
                    : "Unable to place your order."
            );
        }

        cart = [];
        displayCart();

        message.textContent =
            `Order received! Your order number is ${result.order_number}. ` +
            `Total: KSh ${money(result.total_amount)}. ` +
            "Please wait for payment instructions.";

        document.getElementById("checkoutForm").reset();
        document.getElementById("deliveryFields").hidden = true;

    } catch (error) {
        message.textContent = error.message;
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Place Order";
    }
});

// START WEBSITE
async function startWebsite() {
    displayCart();

    await Promise.all([
        loadCategories(),
        loadProducts(),
        loadDeliveryZones()
    ]);
}

startWebsite();

// CUSTOMER AUTHENTICATION
let currentCustomer = null;


function setCustomerAccess(allowed) {
    document.body.classList.toggle("customer-auth-required", !allowed);

    const modal = document.getElementById("accountModal");
    const isPasswordRecovery =
        new URLSearchParams(window.location.search).get("reset-password") === "true";

    if (isPasswordRecovery) {
        modal.hidden = false;
        document.getElementById("authSection").hidden = false;
        document.getElementById("customerDashboard").hidden = true;
        document.getElementById("loginForm").hidden = true;
        document.getElementById("registerForm").hidden = true;
        document.getElementById("forgotPasswordForm").hidden = true;
        document.getElementById("resetPasswordForm").hidden = false;
        return;
    }

    if (allowed) {
        modal.hidden = true;
        return;
    }

    modal.hidden = false;
    document.getElementById("authSection").hidden = false;
    document.getElementById("customerDashboard").hidden = true;
    document.getElementById("loginForm").hidden = false;
    document.getElementById("registerForm").hidden = true;

    ["forgotPasswordForm", "resetPasswordForm"].forEach(id => {
        const form = document.getElementById(id);
        if (form) form.hidden = true;
    });
}



const accountModal = document.getElementById("accountModal");

document.getElementById("accountButton").addEventListener("click", () => {
    accountModal.hidden = false;
});

document.getElementById("closeAccount").addEventListener("click", () => {
    accountModal.hidden = true;
});

accountModal.addEventListener("click", event => {
    if (event.target === accountModal) {
        accountModal.hidden = true;
    }
});

document.getElementById("showLogin").addEventListener("click", () => {
    document.getElementById("loginForm").hidden = false;
    document.getElementById("registerForm").hidden = true;
    document.getElementById("accountMessage").textContent = "";
});

document.getElementById("showRegister").addEventListener("click", () => {
    document.getElementById("loginForm").hidden = true;
    document.getElementById("registerForm").hidden = false;
    document.getElementById("accountMessage").textContent = "";
});


// CUSTOMER REGISTRATION - SUPABASE
document.getElementById("registerForm").addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("accountMessage");
    const password = document.getElementById("registerPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (password !== confirmPassword) {
        message.textContent = "Passwords do not match.";
        return;
    }

    const email = document.getElementById("registerEmail").value.trim().toLowerCase();
    const fullName = document.getElementById("registerName").value.trim();
    const phone = document.getElementById("registerPhone").value.trim();

    try {
        const { data, error } = await window.finneySupabase.auth.signUp({
            email,
            password,
            options: {
                emailRedirectTo: window.location.origin + "/",
                data: {
                    full_name: fullName,
                    phone: phone
                }
            }
        });

        if (error) throw error;

        event.target.reset();
        message.textContent = "Account created successfully! You can now sign in using your email and password.";
    } catch (error) {
        message.textContent = error.message || "Unable to create your account.";
    }
});

// CUSTOMER LOGIN - SUPABASE
document.getElementById("loginForm").addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("accountMessage");
    const email = document.getElementById("loginIdentifier").value.trim().toLowerCase();
    const password = document.getElementById("loginPassword").value;

    if (!email.includes("@")) {
        message.textContent = "Please sign in using your registered email address.";
        return;
    }

    try {
        const { data, error } = await window.finneySupabase.auth.signInWithPassword({
            email,
            password
        });

        if (error) throw error;

        const response = await fetch("/api/auth/supabase-session", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + data.session.access_token
            }
        });

        const result = await response.json();

        if (!response.ok) {
            await window.finneySupabase.auth.signOut();
            throw new Error(result.detail || "Unable to connect your customer account.");
        }

        currentCustomer = result.user;
        setCustomerAccess(true);
        event.target.reset();
        message.textContent = result.message;

        await showCustomerDashboard();
    } catch (error) {
        message.textContent = error.message || "Unable to sign in.";
    }
});

// CUSTOMER DASHBOARD DISPLAY
async function showCustomerDashboard() {
    document.getElementById("authSection").hidden = true;
    document.getElementById("customerDashboard").hidden = false;

    document.getElementById("customerWelcome").textContent =
        "Welcome, " + currentCustomer.full_name + "!";

    await loadCustomerView("profile");
}

// CHECK EXISTING SESSION
async function checkCustomerSession() {
    try {
        const { data, error } = await window.finneySupabase.auth.getSession();
        if (error) throw error;

        if (!data.session) {
            setCustomerAccess(false);
            return;
        }

        const response = await fetch("/api/auth/supabase-session", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + data.session.access_token
            }
        });

        if (!response.ok) {
            console.error("Session verification failed:", response.status);
            setCustomerAccess(false);
            return;
        }

        const result = await response.json();
        currentCustomer = result.user;
        setCustomerAccess(true);
        document.getElementById("accountButton").textContent = "My Account";

    } catch (error) {
        console.error("Session check failed:", error);
        setCustomerAccess(false);
    }
}

// CUSTOMER LOGOUT
document.getElementById("logoutButton").addEventListener("click", async () => {
    try {
        await window.finneySupabase.auth.signOut();

        await fetch("/api/auth/logout", {
            method: "POST",
            credentials: "same-origin"
        });

        currentCustomer = null;
        setCustomerAccess(false);

        document.getElementById("customerDashboard").hidden = true;
        document.getElementById("authSection").hidden = false;
        document.getElementById("loginForm").hidden = false;
        document.getElementById("registerForm").hidden = true;

        document.getElementById("accountMessage").textContent =
            "You have signed out successfully.";

        document.getElementById("accountButton").textContent = "My Account";

    } catch (error) {
        alert("Unable to sign out. Please try again.");
    }
});


// CUSTOMER DASHBOARD FUNCTIONS

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}

async function accountRequest(url, options = {}) {
    const { data } = await window.finneySupabase.auth.getSession();
    const token = data.session?.access_token;

    if (!token) throw new Error("Please sign in to continue.");

    const response = await fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            "Authorization": "Bearer " + token,
            ...options.headers
        }
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            typeof result.detail === "string"
                ? result.detail
                : "Unable to load account information."
        );
    }

    return result;
}

// TOP NAVIGATION FAVOURITES BUTTON
document.getElementById("favoritesButton").addEventListener("click", async () => {
    if (!currentCustomer) {
        document.getElementById("accountModal").hidden = false;
        document.getElementById("accountMessage").textContent =
            "Please sign in to view your favourite meals.";
        return;
    }

    document.getElementById("accountModal").hidden = false;
    await showCustomerDashboard();
    await loadCustomerView("favorites");
});
// TOP NAVIGATION TRACK ORDER BUTTON
document.getElementById("trackOrderButton").addEventListener("click", async () => {
    if (!currentCustomer) {
        document.getElementById("accountModal").hidden = false;
        document.getElementById("accountMessage").textContent =
            "Please sign in to track your orders.";
        return;
    }

    document.getElementById("accountModal").hidden = false;
    document.getElementById("authSection").hidden = true;
    document.getElementById("customerDashboard").hidden = false;
    document.getElementById("customerWelcome").textContent = "Track My Orders";
    document.querySelector(".customer-nav").hidden = true;
    await loadCustomerView("orders");
});
// DASHBOARD NAVIGATION
document.querySelectorAll("[data-account-view]").forEach(button => {
    button.addEventListener("click", () => {
        loadCustomerView(button.dataset.accountView);
    });
});

// LOAD SELECTED DASHBOARD SECTION
async function loadCustomerView(view) {
    const container = document.getElementById("customerAccountContent");
    container.textContent = "Loading...";

    try {
        if (view === "profile") {
            const data = await accountRequest("/api/customer/profile");

            container.innerHTML = `
                <h3>My Profile</h3>
                <p><strong>Name:</strong> ${escapeHTML(data.full_name)}</p>
                <p><strong>Email:</strong> ${escapeHTML(data.email)}</p>
                <p><strong>Phone:</strong> ${escapeHTML(data.phone)}</p>
                <p><strong>Customer ID:</strong> ${data.id}</p>
            `;
        }

        else if (view === "orders") {
            const orders = await accountRequest("/api/customer/orders");

            if (!orders.length) {
                container.textContent = "You have not placed any orders yet.";
                return;
            }

            container.innerHTML = `
                <h3>Track My Orders</h3>
                ${orders.length ? orders.map(order => `
                    <div class="account-order">
                        <h4>Order ${escapeHTML(order.order_number)}</h4>
                        <p><strong>Status:</strong> ${escapeHTML(order.status)}</p>
                        <p><strong>Payment:</strong> ${escapeHTML(order.payment_status)}</p>
                        <p><strong>Order type:</strong> ${escapeHTML(order.order_type || "Not specified")}</p>
                        ${order.delivery_address ? `<p><strong>Address:</strong> ${escapeHTML(order.delivery_address)}</p>` : ""}
                        ${order.mpesa_reference ? `<p><strong>M-Pesa reference:</strong> ${escapeHTML(order.mpesa_reference)}</p>` : ""}
                        <p><strong>Total:</strong> KSh ${money(Number(order.total_amount))}</p>
                        <p><strong>Placed:</strong> ${escapeHTML(order.created_at || "")}</p>
                        <p><strong>Updated:</strong> ${escapeHTML(order.updated_at || "")}</p>
                        <p><strong>Items:</strong> ${order.items.map(i => `${escapeHTML(i.product_name)} x ${i.quantity}`).join(", ")}</p>
                    </div>
                `).join("") : "<p>No orders yet.</p>"}
            `;
        }

        else if (view === "favorites") {
            const favorites = await accountRequest("/api/customer/favorites");

            if (!favorites.length) {
                container.textContent = "You have not saved any favourite meals.";
                return;
            }

            container.innerHTML = `
                <h3>My Favourite Meals</h3>
                ${favorites.map(item => `
                    <div class="account-favorite">
                        <h4>${escapeHTML(item.name)}</h4>
                        <p>KSh ${money(Number(item.price))}</p>
                        <p>${item.is_available ? "Available" : "Currently unavailable"}</p>
                        <button class="primary-button"
                            data-add-favorite="${item.product_id}"
                            ${!item.is_available ? "disabled" : ""}>
                            Add to Cart
                        </button>
                        <button data-remove-favorite="${item.product_id}">
                            Remove
                        </button>
                    </div>
                `).join("")}
            `;

            container.querySelectorAll("[data-add-favorite]").forEach(button => {
                button.addEventListener("click", () => {
                    addToCart(Number(button.dataset.addFavorite));
                });
            });

            container.querySelectorAll("[data-remove-favorite]").forEach(button => {
                button.addEventListener("click", async () => {
                    try {
                        await accountRequest(
                            `/api/customer/favorites/${button.dataset.removeFavorite}`,
                            { method: "DELETE" }
                        );

                        await loadCustomerView("favorites");
                    } catch (error) {
                        alert(error.message);
                    }
                });
            });
        }

        else if (view === "loyalty") {
            const data = await accountRequest("/api/customer/loyalty");

            container.innerHTML = `
                <h3>My Loyalty Rewards</h3>
                <p>Completed orders: ${data.completed_orders}</p>
                <p>Available points: ${data.points_balance}</p>
                <p>Lifetime points: ${data.lifetime_points}</p>
                <p>Orders until next reward: ${data.orders_until_reward}</p>
                <p>Every 6 completed orders earns 150 points.</p>
            `;
        }

        else if (view === "preferences") {
            const data = await accountRequest("/api/customer/preferences");

            container.innerHTML = `
                <h3>My Preferences</h3>
                <p>Preferred delivery location:
                    ${escapeHTML(data.preferred_delivery_location || "Not selected")}
                </p>
                <p>Favourite categories:
                    ${escapeHTML((data.favorite_categories || []).join(", ") || "None")}
                </p>
                <p>Recently viewed meal IDs:
                    ${escapeHTML((data.recently_viewed || []).join(", ") || "None")}
                </p>
                <p>Your preferences are linked to your customer account.</p>
            `;
        }

    } catch (error) {
        container.textContent = error.message;
    }
}

async function loadCustomerView(view) {
    const container = document.getElementById("customerAccountContent");
    container.textContent = "Loading...";

    try {
        if (view === "addresses") {
            const addresses = await accountRequest("/api/customer/addresses");

            container.innerHTML = `
                <h3>Saved Addresses</h3>
                <form id="addressForm" class="account-form">
                    <input name="label" placeholder="Label (Home, Work)" value="Home">
                    <input name="recipient_name" placeholder="Recipient name" required>
                    <input name="phone" placeholder="Phone number" required>
                    <input name="county" placeholder="County" required>
                    <input name="town" placeholder="Town" required>
                    <input name="estate" placeholder="Estate" required>
                    <input name="building" placeholder="Building">
                    <input name="house_number" placeholder="House number">
                    <textarea name="instructions" placeholder="Delivery instructions"></textarea>
                    <label><input type="checkbox" name="is_default"> Set as default</label>
                    <button class="primary-button">Save Address</button>
                </form>
                ${addresses.map(a => `
                    <div class="account-order">
                        <h4>${escapeHTML(a.label)}</h4>
                        <p>${escapeHTML(a.recipient_name)} - ${escapeHTML(a.phone)}</p>
                        <p>${escapeHTML(a.estate)}, ${escapeHTML(a.town)}, ${escapeHTML(a.county)}</p>
                        <p>${a.is_default ? "Default address" : ""}</p>
                        <button data-default-address="${a.id}">Set Default</button>
                        <button data-delete-address="${a.id}">Delete</button>
                    </div>
                `).join("")}
            `;

            document.getElementById("addressForm").addEventListener("submit", async e => {
                e.preventDefault();
                const form = new FormData(e.target);
                const data = Object.fromEntries(form.entries());
                data.is_default = form.has("is_default");

                await accountRequest("/api/customer/addresses", {
                    method: "POST",
                    body: JSON.stringify(data)
                });
                loadCustomerView("addresses");
            });

            container.querySelectorAll("[data-delete-address]").forEach(button => {
                button.onclick = async () => {
                    await accountRequest(`/api/customer/addresses/${button.dataset.deleteAddress}`, {method:"DELETE"});
                    loadCustomerView("addresses");
                };
            });

            container.querySelectorAll("[data-default-address]").forEach(button => {
                button.onclick = async () => {
                    await accountRequest(`/api/customer/addresses/${button.dataset.defaultAddress}/default`, {method:"POST"});
                    loadCustomerView("addresses");
                };
            });
        }

        else if (view === "payments") {
            const payments = await accountRequest("/api/customer/payments");
            container.innerHTML = `
                <h3>Payment History</h3>
                ${payments.length ? payments.map(p => `
                    <div class="account-order">
                        <h4>${escapeHTML(p.order_number)}</h4>
                        <p>Amount: KSh ${money(Number(p.amount))}</p>
                        <p>Payment: ${escapeHTML(p.payment_status)}</p>
                        <p>M-Pesa reference: ${escapeHTML(p.mpesa_reference || "Not provided")}</p>
                        <p>Date: ${escapeHTML(p.date || "")}</p>
                    </div>
                `).join("") : "<p>No payment records found.</p>"}
            `;
        }

        else if (view === "notifications") {
            const data = await accountRequest("/api/customer/notifications");
            container.innerHTML = `
                <h3>Notifications (${data.unread_count} unread)</h3>
                <button id="readAllNotifications">Mark All as Read</button>
                ${data.notifications.length ? data.notifications.map(n => `
                    <div class="account-order">
                        <h4>${escapeHTML(n.title)}</h4>
                        <p>${escapeHTML(n.message)}</p>
                        <small>${escapeHTML(n.created_at || "")}</small>
                        <p>${n.is_read ? "Read" : "Unread"}</p>
                        ${!n.is_read ? `<button data-read-notification="${n.id}">Mark Read</button>` : ""}
                    </div>
                `).join("") : "<p>No notifications yet.</p>"}
            `;

            document.getElementById("readAllNotifications").onclick = async () => {
                await accountRequest("/api/customer/notifications/read-all", {method:"POST"});
                loadCustomerView("notifications");
            };

            container.querySelectorAll("[data-read-notification]").forEach(button => {
                button.onclick = async () => {
                    await accountRequest(`/api/customer/notifications/${button.dataset.readNotification}/read`, {method:"PUT"});
                    loadCustomerView("notifications");
                };
            });
        }

        else if (view === "settings") {
            const data = await accountRequest("/api/customer/profile");
            container.innerHTML = `
                <h3>Account Settings</h3>
                <form id="profileSettingsForm" class="account-form">
                    <input name="full_name" value="${escapeHTML(data.full_name)}" placeholder="Full name" required>
                    <input name="email" type="email" value="${escapeHTML(data.email)}" placeholder="Email" required>
                    <input name="phone" value="${escapeHTML(data.phone || "")}" placeholder="Phone">
                    <button class="primary-button">Update Profile</button>
                </form>
                <h3>Change Password</h3>
                <form id="passwordSettingsForm" class="account-form">
                    <input name="current_password" type="password" placeholder="Current password" required>
                    <input name="new_password" type="password" placeholder="New password (8+ characters)" required minlength="8">
                    <button class="primary-button">Change Password</button>
                </form>
            `;

            document.getElementById("profileSettingsForm").onsubmit = async e => {
                e.preventDefault();
                const data = Object.fromEntries(new FormData(e.target).entries());
                await accountRequest("/api/customer/profile", {
                    method:"PUT", body:JSON.stringify(data)
                });
                alert("Profile updated successfully.");
                loadCustomerView("settings");
            };

            document.getElementById("passwordSettingsForm").onsubmit = async e => {
                e.preventDefault();
                const data = Object.fromEntries(new FormData(e.target).entries());
                await accountRequest("/api/customer/password", {
                    method:"PUT", body:JSON.stringify(data)
                });
                alert("Password updated successfully.");
                e.target.reset();
            };
        }

        else if (view === "profile") {
            const data = await accountRequest("/api/customer/profile");
            container.innerHTML = `
                <h3>My Profile</h3>
                <p>Name: ${escapeHTML(data.full_name)}</p>
                <p>Email: ${escapeHTML(data.email)}</p>
                <p>Phone: ${escapeHTML(data.phone || "")}</p>
                <p>Customer ID: ${data.id}</p>
            `;
        }

        else if (view === "orders") {
            const orders = await accountRequest("/api/customer/orders");
            container.innerHTML = `
                <h3>My Orders</h3>
                ${orders.length ? orders.map(order => `
                    <div class="account-order">
                        <h4>${escapeHTML(order.order_number)}</h4>
                        <p>Status: ${escapeHTML(order.status)}</p>
                        <p>Payment: ${escapeHTML(order.payment_status)}</p>
                        <p>Total: KSh ${money(Number(order.total_amount))}</p>
                        <p>${order.items.map(i => `${escapeHTML(i.product_name)} x ${i.quantity}`).join(", ")}</p>
                    </div>
                `).join("") : "<p>No orders yet.</p>"}
            `;
        }

        else if (view === "favorites") {
            const favorites = await accountRequest("/api/customer/favorites");
            container.innerHTML = `
                <h3>My Favourite Meals</h3>
                ${favorites.length ? favorites.map(item => `
                    <div class="account-favorite">
                        <h4>${escapeHTML(item.name)}</h4>
                        <p>KSh ${money(Number(item.price))}</p>
                        <button data-add-favorite="${item.product_id}">Add to Cart</button>
                        <button data-remove-favorite="${item.product_id}">Remove</button>
                    </div>
                `).join("") : "<p>No favourite meals saved.</p>"}
            `;
            container.querySelectorAll("[data-add-favorite]").forEach(b => {
                b.onclick = () => addToCart(Number(b.dataset.addFavorite));
            });
            container.querySelectorAll("[data-remove-favorite]").forEach(b => {
                b.onclick = async () => {
                    await accountRequest(`/api/customer/favorites/${b.dataset.removeFavorite}`, {method:"DELETE"});
                    loadCustomerView("favorites");
                };
            });
        }

        else if (view === "loyalty") {
            const data = await accountRequest("/api/customer/loyalty");
            container.innerHTML = `
                <h3>My Loyalty Rewards</h3>
                <p>Completed orders: ${data.completed_orders}</p>
                <p>Available points: ${data.points_balance}</p>
                <p>Lifetime points: ${data.lifetime_points}</p>
                <p>Orders until next reward: ${data.orders_until_reward}</p>
            `;
        }

        else if (view === "preferences") {
            const data = await accountRequest("/api/customer/preferences");
            container.innerHTML = `
                <h3>My Preferences</h3>
                <p>Preferred delivery location: ${escapeHTML(data.preferred_delivery_location || "Not selected")}</p>
                <p>Favourite categories: ${escapeHTML((data.favorite_categories || []).join(", ") || "None")}</p>
                <p>Recently viewed: ${escapeHTML((data.recently_viewed || []).join(", ") || "None")}</p>
            `;
        }

    } catch (error) {
        container.textContent = error.message;
    }
}
// RESTORE CUSTOMER SESSION WHEN WEBSITE OPENS
checkCustomerSession();











// FORGOT PASSWORD
document.getElementById("forgotPasswordLink").addEventListener("click", event => {
    event.preventDefault();

    document.getElementById("loginForm").hidden = true;
    document.getElementById("registerForm").hidden = true;
    document.getElementById("forgotPasswordForm").hidden = false;
    document.getElementById("accountMessage").textContent = "";
});

document.getElementById("backToLogin").addEventListener("click", () => {
    document.getElementById("forgotPasswordForm").hidden = true;
    document.getElementById("loginForm").hidden = false;
    document.getElementById("accountMessage").textContent = "";
});

document.getElementById("forgotPasswordForm").addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("accountMessage");
    const email = document.getElementById("forgotPasswordEmail").value.trim();

    try {
        const { error } = await window.finneySupabase.auth.resetPasswordForEmail(email, {
            redirectTo: window.location.origin + "/?reset-password=true"
        });

        if (error) throw error;

        message.textContent = "If an account exists for that email, a password recovery link has been sent.";
        event.target.reset();
    } catch (error) {
        message.textContent = error.message || "Unable to send the recovery email.";
    }
});



// SUPABASE PASSWORD RECOVERY
function showPasswordResetForm() {
    document.getElementById("accountModal").hidden = false;
    document.getElementById("loginForm").hidden = true;
    document.getElementById("registerForm").hidden = true;
    document.getElementById("forgotPasswordForm").hidden = true;
    document.getElementById("resetPasswordForm").hidden = false;
    document.getElementById("accountMessage").textContent =
        "Enter and confirm your new password.";
}

if (new URLSearchParams(window.location.search).get("reset-password") === "true") {
    showPasswordResetForm();
}

document.getElementById("resetPasswordForm").addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("accountMessage");
    const password = document.getElementById("newPassword").value;
    const confirmation = document.getElementById("confirmNewPassword").value;

    if (password.length < 8) {
        message.textContent = "Your password must contain at least 8 characters.";
        return;
    }

    if (password !== confirmation) {
        message.textContent = "Passwords do not match.";
        return;
    }

    try {
        const { error } = await window.finneySupabase.auth.updateUser({
            password: password
        });

        if (error) throw error;

        await window.finneySupabase.auth.signOut();

        event.target.reset();
        event.target.hidden = true;
        document.getElementById("loginForm").hidden = false;
        message.textContent = "Password updated successfully. You can now sign in.";

        window.history.replaceState({}, document.title, window.location.pathname);
    } catch (error) {
        message.textContent = error.message || "Unable to update your password.";
    }
});


// FINNEY BITES ACCOUNT NAVIGATION
function finneyShowAccountForm(formName) {
    const modal = document.getElementById("accountModal");
    const auth = document.getElementById("authSection");
    const dashboard = document.getElementById("customerDashboard");

    if (modal) modal.hidden = false;
    if (auth) auth.hidden = false;
    if (dashboard) dashboard.hidden = true;

    ["loginForm", "registerForm", "forgotPasswordForm", "resetPasswordForm"]
        .forEach(id => {
            const form = document.getElementById(id);
            if (form) form.hidden = id !== formName;
        });

    const message = document.getElementById("accountMessage");
    if (message) message.textContent = "";

    const activeForm = document.getElementById(formName);
    if (activeForm) {
        activeForm.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

document.addEventListener("click", async event => {
    const button = event.target.closest(
        "#accountButton, #showLogin, #showRegister, #forgotPasswordLink, #backToLogin"
    );

    if (!button) return;

    event.preventDefault();
    event.stopImmediatePropagation();

    if (button.id === "accountButton") {
        if (currentCustomer) {
            document.getElementById("accountModal").hidden = false;
            document.getElementById("authSection").hidden = true;
            document.getElementById("customerDashboard").hidden = false;
            document.querySelector(".customer-nav").hidden = false;
            document.getElementById("customerWelcome").textContent = "Welcome, " + currentCustomer.full_name + "!";
            await loadCustomerView("profile");
        } else {
            finneyShowAccountForm("loginForm");
        }
    } else if (button.id === "showLogin" || button.id === "backToLogin") {
        finneyShowAccountForm("loginForm");
    } else if (button.id === "showRegister") {
        finneyShowAccountForm("registerForm");
    } else if (button.id === "forgotPasswordLink") {
        finneyShowAccountForm("forgotPasswordForm");
    }
}, true);

// Reliable Supabase recovery email submission
document.getElementById("forgotPasswordForm").addEventListener("submit", async event => {
    event.preventDefault();
    event.stopImmediatePropagation();

    const message = document.getElementById("accountMessage");
    const email = document.getElementById("forgotPasswordEmail").value.trim();

    try {
        const { error } = await window.finneySupabase.auth.resetPasswordForEmail(email, {
            redirectTo: window.location.origin + "/?reset-password=true"
        });

        if (error) throw error;

        message.textContent = "If an account exists for this email, a recovery link has been sent.";
        event.target.reset();
    } catch (error) {
        message.textContent = error.message || "Unable to send recovery email.";
    }
}, true);


// Complete Supabase password recovery
window.finneySupabase.auth.onAuthStateChange((event, session) => {
    if (event === "PASSWORD_RECOVERY" && session) {
        finneyShowAccountForm("resetPasswordForm");
        setCustomerAccess(false);
    }
});



