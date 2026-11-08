
    const loginForm = document.getElementById("loginForm");
    const loginSection = document.getElementById("loginSection");
    const dashboardSection = document.getElementById("dashboardSection");
    const logoutButton = document.getElementById("logoutButton");

    let adminOrdersRefreshTimer = null;
    let knownAdminOrderNumbers = null;

    loginForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const message = document.getElementById("message");
        message.textContent = "Signing in...";

        try {
            const response = await fetch("/api/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    email: document.getElementById("email").value,
                    password: document.getElementById("password").value
                })
            });

            const result = await response.json();

            if (!response.ok) {
                message.textContent = result.detail || "Login failed.";
                return;
            }

            if (result.user.role !== "admin") {
                message.textContent = "Administrator access required.";
                await fetch("/api/auth/logout", {
                    method: "POST",
                    credentials: "same-origin"
                });
                return;
            }

            loginSection.style.display = "none";
            dashboardSection.style.display = "block";
            logoutButton.style.display = "block";

            await loadDashboard();
            await loadProducts();

            knownAdminOrderNumbers = null;
            await loadOrders();

            if (adminOrdersRefreshTimer) {
                clearInterval(adminOrdersRefreshTimer);
            }

            adminOrdersRefreshTimer = setInterval(loadOrders, 10000);
            await loadMessages();
            await loadReviews();
            await loadWhatsAppStatus();

        } catch (error) {
            message.textContent = "Unable to connect to the server.";
        }
    });

    async function loadDashboard() {
        const message = document.getElementById("dashboardMessage");
        message.textContent = "Loading dashboard...";

        try {
            const response = await fetch("/api/admin/dashboard", {
                credentials: "same-origin"
            });

            if (!response.ok) {
                message.textContent = "Unable to load dashboard.";
                return;
            }

            const data = await response.json();

            document.getElementById("totalProducts").textContent =
                data.statistics.total_products;

            document.getElementById("totalCategories").textContent =
                data.statistics.total_categories;

            document.getElementById("totalUsers").textContent =
                data.statistics.total_users;

            document.getElementById("totalCustomers").textContent =
                data.statistics.total_customers;

            document.getElementById("totalOrders").textContent =
                data.statistics.total_orders;

            document.getElementById("totalRevenue").textContent =
                "KSh " + Number(data.statistics.total_revenue).toLocaleString("en-KE");

            document.getElementById("pendingPayments").textContent =
                data.statistics.pending_payments;

            message.textContent = "Dashboard loaded successfully.";

        } catch (error) {
            message.textContent = "Server connection failed.";
        }
    }

    async function logout() {
        if (adminOrdersRefreshTimer) {
            clearInterval(adminOrdersRefreshTimer);
            adminOrdersRefreshTimer = null;
        }

        knownAdminOrderNumbers = null;

        await fetch("/api/auth/logout", {
            method: "POST",
            credentials: "same-origin"
        });

        dashboardSection.style.display = "none";
        loginSection.style.display = "block";
        logoutButton.style.display = "none";
        loginForm.reset();
    }

    async function loadProducts() {
        const table = document.getElementById("productsTable");

        table.innerHTML = "<tr><td colspan='6'>Loading products...</td></tr>";

        try {
            const response = await fetch("/api/admin/products", {
                credentials: "same-origin"
            });

            if (!response.ok) {
                throw new Error("Unable to load products.");
            }

            const data = await response.json();

            table.innerHTML = "";

            data.products.forEach(product => {
                const row = document.createElement("tr");

                const values = [
                    product.id,
                    product.name,
                    "KSh " + product.price,
                    product.stock_quantity,
                    product.is_available ? "Yes" : "No"
                ];

                values.forEach(value => {
                    const cell = document.createElement("td");
                    cell.style.padding = "12px";
                    cell.textContent = value;
                    row.appendChild(cell);
                });

                const actions = document.createElement("td");
                actions.style.padding = "12px";

                const editButton = document.createElement("button");
                editButton.textContent = "Edit";
                editButton.style.marginRight = "8px";
                editButton.addEventListener("click", () => {
                    editProduct(product.id, product.price, product.stock_quantity);
                });
                actions.appendChild(editButton);

                if (product.is_available) {
                    const button = document.createElement("button");
                    button.textContent = "Deactivate";

                    button.addEventListener("click", () => {
                        deactivateProduct(product.id);
                    });

                    actions.appendChild(button);
                } else {
                    const button = document.createElement("button");
                    button.textContent = "Activate";
                    button.addEventListener("click", () => {
                        activateProduct(product.id);
                    });
                    actions.appendChild(button);
                }

                row.appendChild(actions);
                table.appendChild(row);
            });

        } catch (error) {
            table.innerHTML = "<tr><td colspan='6'>"
                + error.message + "</td></tr>";
        }
    }

    document.getElementById("productForm").addEventListener(
        "submit",
        async function(event) {
            event.preventDefault();

            const message = document.getElementById("productMessage");
            message.textContent = "Adding product...";

            const product = {
                name: document.getElementById("productName").value,
                category_id: Number(document.getElementById("categoryId").value),
                description: document.getElementById("productDescription").value,
                price: document.getElementById("productPrice").value,
                stock_quantity: Number(document.getElementById("productStock").value),
                is_available: true,
                is_featured: false
            };

            try {
                const response = await fetch("/api/admin/products", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    credentials: "same-origin",
                    body: JSON.stringify(product)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || "Product creation failed.");
                }

                message.textContent = "Product added successfully.";

                this.reset();
                await loadProducts();

            } catch (error) {
                message.textContent = error.message;
            }
        }
    );

    async function deactivateProduct(productId) {
        if (!confirm("Are you sure you want to deactivate this product?")) {
            return;
        }

        try {
            const response = await fetch(
                "/api/admin/products/" + productId,
                {
                    method: "DELETE",
                    credentials: "same-origin"
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Deactivation failed.");
            }

            alert("Product deactivated successfully.");
            await loadProducts();

        } catch (error) {
            alert(error.message);
        }
    }


    
    async function editProduct(productId, currentPrice, currentStock) {
        const newPrice = prompt("Enter the new product price (KSh):", currentPrice);

        if (newPrice === null) return;

        const newStock = prompt("Enter the new stock quantity:", currentStock);

        if (newStock === null) return;

        const price = Number(newPrice);
        const stock = Number(newStock);

        if (!Number.isFinite(price) || price <= 0) {
            alert("Enter a valid price greater than zero.");
            return;
        }

        if (!Number.isInteger(stock) || stock < 0) {
            alert("Enter a valid stock quantity (0 or more).");
            return;
        }

        try {
            const response = await fetch(
                "/api/admin/products/" + productId,
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    credentials: "same-origin",
                    body: JSON.stringify({
                        price: price,
                        stock_quantity: stock
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Product update failed.");
            }

            alert("Product price and quantity updated successfully!");
            await loadProducts();

        } catch (error) {
            alert(error.message);
        }
    }
    async function activateProduct(productId) {
        if (!confirm("Activate this product?")) {
            return;
        }

        try {
            const response = await fetch(
                "/api/admin/products/" + productId,
                {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    credentials: "same-origin",
                    body: JSON.stringify({
                        is_available: true
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Activation failed.");
            }

            alert("Product activated successfully.");
            await loadProducts();

        } catch (error) {
            alert(error.message);
        }
    }

    async function loadOrders() {
        const pendingTable = document.getElementById("ordersTable");
        const historyTable = document.getElementById("orderHistoryTable");
        const pendingMessage = document.getElementById("ordersMessage");
        const historyMessage = document.getElementById("orderHistoryMessage");

        pendingTable.innerHTML = "";
        historyTable.innerHTML = "";

        pendingMessage.textContent = "Loading orders...";
        historyMessage.textContent = "Loading order history...";

        try {
            const response = await fetch("/api/admin/orders", {
                credentials: "same-origin"
            });

            const orders = await response.json();

            if (!response.ok) {
                throw new Error(orders.detail || "Unable to load orders.");
            }

            const currentOrderNumbers = orders.map(
                order => order.order_number
            );

            if (knownAdminOrderNumbers !== null) {
                const newOrders = orders.filter(
                    order => !knownAdminOrderNumbers.includes(order.order_number)
                );

                if (newOrders.length > 0) {
                    alert("New customer order received: " +
                        newOrders.map(order => order.order_number).join(", "));
                }
            }

            knownAdminOrderNumbers = currentOrderNumbers;

            const pendingOrders = orders.filter(
                order => order.payment_status !== "paid"
            );

            const paidOrders = orders.filter(
                order => order.payment_status === "paid"
            );

            function displayOrders(orderList, table, message, emptyText) {
                if (orderList.length === 0) {
                    message.textContent = emptyText;
                    table.innerHTML =
                        '<tr><td colspan="8" style="padding:15px;">' +
                        emptyText + '</td></tr>';
                    return;
                }

                message.textContent = orderList.length + " orders loaded.";

                orderList.forEach(order => {
                    const row = document.createElement("tr");

                    const items = order.items.map(item =>
                        item.product_name + " x " + item.quantity
                    ).join(", ");

                    const values = [
                        order.order_number,
                        order.customer_name + " (" + order.customer_phone + ")",
                        items,
                        "KSh " + Number(order.total_amount).toLocaleString(),
                        order.mpesa_reference || "Not submitted",
                        order.payment_status,
                        order.status
                    ];

                    values.forEach(value => {
                        const cell = document.createElement("td");
                        cell.style.padding = "12px";
                        cell.textContent = value;
                        row.appendChild(cell);
                    });

                    const actions = document.createElement("td");
                    actions.style.padding = "12px";

                    if (order.status === "received") {
                        const confirmButton = document.createElement("button");
                        confirmButton.textContent = "Confirm Order";
                        confirmButton.onclick = () =>
                            confirmOrder(order.order_number);
                        actions.appendChild(confirmButton);
                    }

                    if (order.payment_status !== "paid" &&
                        order.mpesa_reference &&
                        order.status !== "cancelled") {
                        const verifyButton = document.createElement("button");
                        verifyButton.textContent = "Verify Payment";
                        verifyButton.style.marginTop = "6px";
                        verifyButton.onclick = () => verifyPayment(
                            order.order_number,
                            order.mpesa_reference,
                            order.total_amount
                        );
                        actions.appendChild(verifyButton);
                    }

                    if (order.status === "confirmed" &&
                        order.payment_status === "paid") {
                        const completeButton = document.createElement("button");
                        completeButton.textContent = "Complete Order";
                        completeButton.style.marginTop = "6px";
                        completeButton.onclick = () =>
                            completeOrder(order.order_number);
                        actions.appendChild(completeButton);
                    }

                    if (actions.children.length === 0) {
                        actions.textContent = "No available actions.";
                    }

                    row.appendChild(actions);
                    table.appendChild(row);
                });
            }

            displayOrders(
                pendingOrders,
                pendingTable,
                pendingMessage,
                "No unpaid orders awaiting verification."
            );

            displayOrders(
                paidOrders,
                historyTable,
                historyMessage,
                "No verified payments yet."
            );

        } catch (error) {
            pendingMessage.textContent = error.message;
            historyMessage.textContent = error.message;
        }
    }
    async function confirmOrder(orderNumber) {
        if (!confirm("Confirm order " + orderNumber + "? Stock will be deducted.")) {
            return;
        }

        try {
            const response = await fetch(
                "/api/admin/orders/" + encodeURIComponent(orderNumber) + "/confirm",
                {
                    method: "POST",
                    credentials: "same-origin"
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Order confirmation failed.");
            }

            alert(result.message);
            await loadOrders();
            await loadMessages();
            await loadProducts();

        } catch (error) {
            alert(error.message);
        }
    }

    async function verifyPayment(orderNumber, currentReference, orderTotal) {
        const reference = prompt(
            "Enter the M-Pesa reference:",
            currentReference
        );

        if (reference === null) return;

        const amount = prompt(
            "Enter the amount received (KSh):",
            orderTotal
        );

        if (amount === null) return;

        if (!confirm("Have you confirmed this transaction in your M-Pesa statement?")) {
            alert("Payment was not verified.");
            return;
        }

        const receivedAmount = Number(amount);

        if (!Number.isFinite(receivedAmount) || receivedAmount <= 0) {
            alert("Enter a valid payment amount.");
            return;
        }

        try {
            const response = await fetch(
                "/api/admin/orders/" + encodeURIComponent(orderNumber) + "/verify-payment",
                {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    credentials: "same-origin",
                    body: JSON.stringify({
                        mpesa_reference: reference.trim().toUpperCase(),
                        received_amount: receivedAmount,
                        confirmed_in_statement: true
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Payment verification failed.");
            }

            alert(result.message);
            await loadOrders();
            await loadMessages();

        } catch (error) {
            alert(error.message);
        }
    }
    async function completeOrder(orderNumber) {
        if (!confirm("Mark order " + orderNumber + " as completed?")) return;

        try {
            const response = await fetch(
                "/api/admin/orders/" + encodeURIComponent(orderNumber) + "/complete",
                {
                    method: "POST",
                    credentials: "same-origin"
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Unable to complete order.");
            }

            alert(result.message);
            await loadOrders();
            await loadMessages();

        } catch (error) {
            alert(error.message);
        }
    }
    async function loadMessages() {
        const table = document.getElementById("messagesTable");
        const message = document.getElementById("messagesMessage");

        table.innerHTML = "";
        message.textContent = "Loading customer messages...";

        try {
            const response = await fetch("/api/admin/messages", {
                credentials: "same-origin"
            });

            const messages = await response.json();

            if (!response.ok) {
                throw new Error(messages.detail || "Unable to load messages.");
            }

            if (messages.length === 0) {
                message.textContent = "No customer messages found.";
                table.innerHTML =
                    '<tr><td colspan="7">No messages available.</td></tr>';
                return;
            }

            message.textContent = messages.length + " messages loaded.";

            messages.forEach(item => {
                const row = document.createElement("tr");

                [
                    item.name,
                    item.email,
                    item.phone || "Not provided",
                    item.subject,
                    item.message,
                    item.status
                ].forEach(value => {
                    const cell = document.createElement("td");
                    cell.style.padding = "12px";
                    cell.textContent = value;
                    row.appendChild(cell);
                });

                const actions = document.createElement("td");
                actions.style.padding = "12px";

                if (item.status === "new") {
                    const readButton = document.createElement("button");
                    readButton.textContent = "Mark Read";
                    readButton.onclick = () =>
                        updateMessageStatus(item.id, "read");
                    actions.appendChild(readButton);
                }

                if (item.status !== "resolved") {
                    const resolveButton = document.createElement("button");
                    resolveButton.textContent = "Resolve";
                    resolveButton.style.marginTop = "6px";
                    resolveButton.onclick = () =>
                        updateMessageStatus(item.id, "resolved");
                    actions.appendChild(resolveButton);
                }

                if (actions.children.length === 0) {
                    actions.textContent = "Resolved";
                }

                row.appendChild(actions);
                table.appendChild(row);
            });

        } catch (error) {
            message.textContent = error.message;
        }
    }

    async function updateMessageStatus(messageId, newStatus) {
        try {
            const response = await fetch(
                "/api/admin/messages/" + messageId +
                "/status?status=" + encodeURIComponent(newStatus),
                {
                    method: "PATCH",
                    credentials: "same-origin"
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Unable to update message.");
            }

            alert(result.message);
            await loadMessages();

        } catch (error) {
            alert(error.message);
        }
    }
    async function loadReviews() {
        const table = document.getElementById("reviewsTable");
        const message = document.getElementById("reviewsMessage");

        table.innerHTML = "";
        message.textContent = "Loading reviews...";

        try {
            const response = await fetch("/api/admin/reviews/pending", {
                credentials: "same-origin"
            });

            const reviews = await response.json();

            if (!response.ok) {
                throw new Error(reviews.detail || "Unable to load reviews.");
            }

            if (reviews.length === 0) {
                message.textContent = "No pending reviews found.";
                table.innerHTML =
                    '<tr><td colspan="6">No pending reviews available.</td></tr>';
                return;
            }

            message.textContent = reviews.length + " pending reviews loaded.";

            reviews.forEach(review => {
                const row = document.createElement("tr");

                const values = [
                    review.id,
                    review.order_id,
                    review.rating + " / 5",
                    review.comment,
                    review.created_at
                        ? new Date(review.created_at).toLocaleString()
                        : "Not available"
                ];

                values.forEach(value => {
                    const cell = document.createElement("td");
                    cell.style.padding = "12px";
                    cell.textContent = value;
                    row.appendChild(cell);
                });

                const actions = document.createElement("td");
                actions.style.padding = "12px";

                const approveButton = document.createElement("button");
                approveButton.textContent = "Approve";
                approveButton.onclick = () => approveReview(review.id);

                actions.appendChild(approveButton);
                row.appendChild(actions);
                table.appendChild(row);
            });

        } catch (error) {
            message.textContent = error.message;
        }
    }

    async function approveReview(reviewId) {
        if (!confirm("Approve this customer review?")) return;

        try {
            const response = await fetch(
                "/api/admin/reviews/" + reviewId + "/approve",
                {
                    method: "POST",
                    credentials: "same-origin"
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Unable to approve review.");
            }

            alert(result.message);
            await loadReviews();

        } catch (error) {
            alert(error.message);
        }
    }

    async function loadWhatsAppStatus() {
        const configured = document.getElementById("whatsappConfigured");
        const mode = document.getElementById("whatsappMode");
        const message = document.getElementById("whatsappMessage");

        configured.textContent = "Checking...";
        mode.textContent = "Checking...";
        message.textContent = "";

        try {
            const response = await fetch("/api/admin/whatsapp-status", {
                credentials: "same-origin"
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Unable to check WhatsApp status.");
            }

            configured.textContent = result.configured ? "Configured" : "Not configured";
            mode.textContent = result.mode.toUpperCase();
            message.textContent = result.message;

        } catch (error) {
            configured.textContent = "Unavailable";
            mode.textContent = "Unknown";
            message.textContent = error.message;
        }
    }
