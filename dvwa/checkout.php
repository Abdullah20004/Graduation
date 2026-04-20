<?php
session_start();

if (!isset($_SESSION['user_id'])) {
    header('Location: /login.php');
    exit;
}

$conn = new mysqli('db', 'root', 'password', 'dvwa');
if ($conn->connect_error) {
    die("Connection failed");
}

$userId = $_SESSION['user_id'];
$errorMsg = '';

// Fetch cart items
$cartResult = $conn->query("SELECT c.id as cart_id, c.quantity, p.* FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = {$userId}");
$cartItems = $cartResult ? $cartResult->fetch_all(MYSQLI_ASSOC) : [];

if (empty($cartItems)) {
    header('Location: /cart.php');
    exit;
}

// Calculate totals
$subtotal = 0;
foreach ($cartItems as $item) {
    $subtotal += $item['price'] * $item['quantity'];
}
$shipping = ($subtotal > 99) ? 0 : 9.99;
$tax = round($subtotal * 0.08, 2);
$grandTotal = round($subtotal + $shipping + $tax, 2);

// Handle checkout submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $address = $_POST['address'] ?? '';
    $city = $_POST['city'] ?? '';
    $zip = $_POST['zip'] ?? '';
    $shippingAddress = $address . ', ' . $city . ', ' . $zip;

    // VULNERABLE: Direct concatenation → SQL Injection
    $orderQuery = "INSERT INTO orders (user_id, total_amount, status, shipping_address) VALUES ({$userId}, {$grandTotal}, 'confirmed', '{$shippingAddress}')";

    if ($conn->query($orderQuery)) {
        $orderId = $conn->insert_id;
        foreach ($cartItems as $item) {
            $conn->query("INSERT INTO order_items (order_id, product_id, price, quantity) VALUES ({$orderId}, {$item['id']}, {$item['price']}, {$item['quantity']})");
        }
        $conn->query("DELETE FROM cart WHERE user_id = {$userId}");
        header("Location: /orders.php?id={$orderId}&success=1");
        exit;
    } else {
        $errorMsg = "Failed to process order. Please try again.";
    }
}

// Build order items HTML
$itemsHtml = '';
foreach ($cartItems as $item) {
    $lineTotal = number_format($item['price'] * $item['quantity'], 2);
    $imgUrl = !empty($item['image_url']) ? $item['image_url'] : 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=200';
    $itemsHtml .= '
    <div style="display:flex;align-items:center;gap:15px;padding:12px 0;border-bottom:1px solid var(--glass-border);">
        <img src="' . $imgUrl . '" style="width:50px;height:50px;object-fit:cover;border-radius:8px;">
        <div style="flex:1;">
            <div style="font-weight:600;color:var(--text-primary);font-size:14px;">' . htmlspecialchars($item['name']) . '</div>
            <div style="font-size:12px;color:var(--text-muted);">Qty: ' . $item['quantity'] . '</div>
        </div>
        <div style="font-weight:700;color:var(--text-primary);">$' . $lineTotal . '</div>
    </div>';
}

$subtotalFmt    = number_format($subtotal, 2);
$shippingFmt    = ($shipping == 0) ? 'FREE' : '$' . number_format($shipping, 2);
$shippingStyle  = ($shipping == 0) ? 'color:#00b894;font-weight:700;' : '';
$taxFmt         = number_format($tax, 2);
$grandTotalFmt  = number_format($grandTotal, 2);

$alertHtml = '';
if ($errorMsg) {
    $alertHtml = '<div style="background:rgba(255,77,77,0.1);border:1px solid rgba(255,77,77,0.3);color:#ff4d4d;padding:14px 20px;border-radius:10px;margin-bottom:20px;font-size:14px;font-weight:600;">&#10060; ' . htmlspecialchars($errorMsg) . '</div>';
}

$PAGE_CONTENT = <<<HTML
    <div style="margin-bottom:40px;">
        <div class="page-title">
            <span style="font-size:48px;">&#x1F4B3;</span>
            <div>
                <h1 style="margin:0;font-family:'Outfit',sans-serif;">Checkout</h1>
                <p style="font-size:14px;color:var(--text-secondary);font-weight:500;">Complete your order</p>
            </div>
        </div>
    </div>

    {$alertHtml}

    <form method="POST">
        <div style="display:grid;grid-template-columns:1fr 380px;gap:30px;align-items:start;">
            <div>
                <div class="card" style="padding:30px;margin-bottom:20px;">
                    <h3 style="margin-bottom:20px;color:var(--text-primary);">&#x1F4E6; Shipping Address</h3>
                    <div class="form-group">
                        <label>Street Address</label>
                        <input type="text" name="address" placeholder="123 Cyber Drive" required>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
                        <div class="form-group">
                            <label>City</label>
                            <input type="text" name="city" placeholder="Silicon Valley" required>
                        </div>
                        <div class="form-group">
                            <label>ZIP Code</label>
                            <input type="text" name="zip" placeholder="94025" required>
                        </div>
                    </div>
                </div>

                <div class="card" style="padding:30px;">
                    <h3 style="margin-bottom:20px;color:var(--text-primary);">&#x1F4B3; Payment Details</h3>
                    <div class="form-group">
                        <label>Card Number</label>
                        <input type="text" name="card_number" placeholder="4242 4242 4242 4242" required maxlength="19">
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
                        <div class="form-group">
                            <label>Expiry</label>
                            <input type="text" name="expiry" placeholder="MM/YY" required maxlength="5">
                        </div>
                        <div class="form-group">
                            <label>CVV</label>
                            <input type="text" name="cvv" placeholder="123" required maxlength="4">
                        </div>
                    </div>
                </div>
            </div>

            <div class="card" style="padding:30px;position:sticky;top:20px;">
                <h3 style="margin-bottom:20px;color:var(--text-primary);">Order Summary</h3>
                {$itemsHtml}
                <div style="margin-top:15px;padding-top:15px;border-top:1px solid var(--glass-border);">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:14px;color:var(--text-secondary);">
                        <span>Subtotal</span><span>\${$subtotalFmt}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:14px;color:var(--text-secondary);">
                        <span>Shipping</span><span style="{$shippingStyle}">{$shippingFmt}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:15px;font-size:14px;color:var(--text-secondary);">
                        <span>Tax (8%)</span><span>\${$taxFmt}</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding-top:15px;border-top:2px solid var(--accent);font-size:20px;font-weight:800;color:var(--text-primary);">
                        <span>Total</span><span style="color:var(--accent);">\${$grandTotalFmt}</span>
                    </div>
                </div>
                <button type="submit" class="btn" style="width:100%;margin-top:25px;padding:16px;font-size:16px;">
                    Place Order &#x2713;
                </button>
                <p style="margin-top:15px;font-size:11px;color:var(--text-muted);text-align:center;">&#x1F512; Simulated payment for training purposes.</p>
            </div>
        </div>
    </form>
HTML;

$conn->close();
include '/app/templates/app_template.php';
?>