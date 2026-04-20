<?php
session_start();

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
$message = '';

// Handle Actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    $productId = $_POST['product_id'] ?? 0;
    
    // Default to 'add' if product_id is set but action is missing
    if ($action === '' && $productId > 0) {
        $action = 'add';
    }
    
    if ($action === 'add') {
        // Check if item already exists in cart
        $check = $conn->prepare("SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?");
        $check->bind_param("ii", $userId, $productId);
        $check->execute();
        $res = $check->get_result();
        
        if ($res->num_rows > 0) {
            $item = $res->fetch_assoc();
            $newQty = $item['quantity'] + 1;
            $upd = $conn->prepare("UPDATE cart SET quantity = ? WHERE id = ?");
            $upd->bind_param("ii", $newQty, $item['id']);
            $upd->execute();
        } else {
            $ins = $conn->prepare("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)");
            $ins->bind_param("ii", $userId, $productId);
            $ins->execute();
        }
        $message = '<div class="alert alert-success">Product added to cart!</div>';
    } 
    elseif ($action === 'update') {
        $qty = $_POST['quantity'] ?? 1;
        $cartId = $_POST['cart_id'] ?? 0;
        if ($qty <= 0) {
            $del = $conn->prepare("DELETE FROM cart WHERE id = ? AND user_id = ?");
            $del->bind_param("ii", $cartId, $userId);
            $del->execute();
        } else {
            $upd = $conn->prepare("UPDATE cart SET quantity = ? WHERE id = ? AND user_id = ?");
            $upd->bind_param("iii", $qty, $cartId, $userId);
            $upd->execute();
        }
    }
    elseif ($action === 'remove') {
        $cartId = $_POST['cart_id'] ?? 0;
        $del = $conn->prepare("DELETE FROM cart WHERE id = ? AND user_id = ?");
        $del->bind_param("ii", $cartId, $userId);
        $del->execute();
        $message = '<div class="alert alert-info">Item removed from cart.</div>';
    }
}

// Fetch Cart Items
$query = "SELECT c.id as cart_id, c.quantity, p.* 
          FROM cart c 
          JOIN products p ON c.product_id = p.id 
          WHERE c.user_id = $userId";
$result = $conn->query($query);
$cartItems = $result->fetch_all(MYSQLI_ASSOC);

$total = 0;
$cartHtml = '';

if (empty($cartItems)) {
    $cartHtml = <<<HTML
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 20px;">🛒</div>
        <h2 style="margin-bottom: 10px;">Your cart is empty</h2>
        <p style="color: var(--text-secondary); margin-bottom: 30px;">Looks like you haven't added anything to your cart yet.</p>
        <a href="/products.php" class="btn">Start Shopping</a>
    </div>
HTML;
} else {
    foreach ($cartItems as $item) {
        $subtotal = $item['price'] * $item['quantity'];
        $total += $subtotal;
        $imageUrl = !empty($item['image_url']) ? $item['image_url'] : 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=200';
        
        $cartHtml .= <<<HTML
        <div class="card" style="display: flex; align-items: center; gap: 20px; padding: 15px; margin-bottom: 15px;">
            <img src="{$imageUrl}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
            <div style="flex: 1;">
                <h4 style="margin: 0 0 5px 0;">{$item['name']}</h4>
                <p style="margin: 0; color: var(--text-secondary); font-size: 13px;">\${$item['price']} per unit</p>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <form action="/cart.php" method="POST" style="display: flex; align-items: center; gap: 5px;">
                    <input type="hidden" name="action" value="update">
                    <input type="hidden" name="cart_id" value="{$item['cart_id']}">
                    <input type="number" name="quantity" value="{$item['quantity']}" min="1" style="width: 60px; padding: 8px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary);">
                    <button type="submit" class="btn" style="padding: 8px 12px; font-size: 12px;">Update</button>
                </form>
                <form action="/cart.php" method="POST">
                    <input type="hidden" name="action" value="remove">
                    <input type="hidden" name="cart_id" value="{$item['cart_id']}">
                    <button type="submit" style="background: none; border: none; color: #ff7675; cursor: pointer; font-size: 18px;">🗑️</button>
                </form>
            </div>
            <div style="width: 100px; text-align: right; font-weight: 600; color: var(--primary);">
                \${$subtotal}
            </div>
        </div>
HTML;
    }
    
    $cartHtml .= <<<HTML
    <div class="card" style="margin-top: 30px; padding: 25px; display: flex; flex-direction: column; align-items: flex-end;">
        <div style="font-size: 18px; margin-bottom: 10px;">Total Amount: <span style="font-size: 24px; font-weight: 700; color: var(--primary); margin-left: 10px;">\${$total}</span></div>
        <div style="margin-bottom: 20px; color: var(--text-secondary); font-size: 14px;">Shipping and taxes calculated at checkout</div>
        <div style="display: flex; gap: 15px;">
            <a href="/products.php" class="btn" style="background: transparent; border: 1px solid var(--border-color); color: var(--text-primary);">Continue Shopping</a>
            <a href="/checkout.php" class="btn" style="padding: 12px 40px; font-size: 16px;">Proceed to Checkout</a>
        </div>
    </div>
HTML;
}

$PAGE_CONTENT = <<<HTML
<h1 class="page-title">🛒 Shopping Cart</h1>
{$message}
<div style="max-width: 900px; margin: 0 auto;">
    {$cartHtml}
</div>
HTML;

$conn->close();
include '/app/templates/app_template.php';
?>
