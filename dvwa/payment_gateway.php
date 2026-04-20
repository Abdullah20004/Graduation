<?php
session_start();

// Simulated Payment Gateway Endpoint
// This page represents an external provider or a specific payment handling module.
// It is purposely made to demonstrate realistic data flow and potential vulnerabilities (e.g. CSRF).

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    die("Error: This endpoint only accepts POST requests from verified checkouts.");
}

// Redirect if not logged in
if (!isset($_SESSION['user_id'])) {
    header('Location: /login.php');
    exit;
}

$conn = new mysqli('db', 'root', 'password', 'dvwa');
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$userId = $_SESSION['user_id'];
$amount = $_POST['amount'] ?? 0;
$address = $_POST['address'] ?? '';
$card_number = $_POST['card_number'] ?? '';

// Simulated processing delay for realism
usleep(1500000); // 1.5 seconds

// Logic to create the order (moved here from checkout.php to simulate gateway-side processing/callback)
// 1. Create Order
$stmt = $conn->prepare("INSERT INTO orders (user_id, total_amount, status, shipping_address) VALUES (?, ?, 'paid', ?)");
$stmt->bind_param("ids", $userId, $amount, $address);

if ($stmt->execute()) {
    $orderId = $conn->insert_id;
    
    // 2. Fetch cart items for this user
    $query = "SELECT product_id, quantity, price FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = $userId";
    $result = $conn->query($query);
    $cartItems = $result->fetch_all(MYSQLI_ASSOC);
    
    // 3. Move items to order_items
    foreach ($cartItems as $item) {
        $stmtItems = $conn->prepare("INSERT INTO order_items (order_id, product_id, price, quantity) VALUES (?, ?, ?, ?)");
        $stmtItems->bind_param("iidi", $orderId, $item['product_id'], $item['price'], $item['quantity']);
        $stmtItems->execute();
    }
    
    // 4. Clear Cart
    $conn->query("DELETE FROM cart WHERE user_id = $userId");
    
    // Redirect to success page
    header("Location: /checkout.php?status=success&order_id=$orderId");
} else {
    header("Location: /checkout.php?status=error");
}

$conn->close();
?>
