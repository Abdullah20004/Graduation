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
$orderId = isset($_GET['id']) ? (int)$_GET['id'] : 0;
$showSuccess = isset($_GET['success']);

// If specific order requested, show detail
if ($orderId > 0) {
    // VULNERABLE: IDOR - no ownership check, any user can view any order
    $orderResult = $conn->query("SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id WHERE o.id = {$orderId}");
    
    if ($orderResult && $orderResult->num_rows > 0) {
        $order = $orderResult->fetch_assoc();
        $itemsResult = $conn->query("SELECT oi.*, p.name, p.image_url FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = {$orderId}");
        $items = $itemsResult ? $itemsResult->fetch_all(MYSQLI_ASSOC) : [];
        
        $statusColor = match($order['status']) {
            'confirmed' => '#00b894',
            'shipped' => '#0984e3',
            'delivered' => '#6c5ce7',
            default => '#fdcb6e'
        };
        $statusLabel = ucfirst($order['status']);
        $orderDate = date('F j, Y \a\t g:i A', strtotime($order['created_at']));
        
        $itemsHtml = '';
        foreach ($items as $item) {
            $lineTotal = number_format($item['price'] * $item['quantity'], 2);
            $imageUrl = !empty($item['image_url']) ? $item['image_url'] : 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=200';
            $itemsHtml .= <<<HTML
            <div style="display:flex; align-items:center; gap:15px; padding:15px 0; border-bottom:1px solid var(--glass-border);">
                <img src="{$imageUrl}" style="width:60px; height:60px; object-fit:cover; border-radius:8px;">
                <div style="flex:1;">
                    <div style="font-weight:600; color:var(--text-primary);">{$item['name']}</div>
                    <div style="font-size:13px; color:var(--text-muted);">Qty: {$item['quantity']} × \${$item['price']}</div>
                </div>
                <div style="font-weight:700; color:var(--text-primary); font-size:16px;">\${$lineTotal}</div>
            </div>
HTML;
        }
        
        $successBanner = '';
        if ($showSuccess) {
            $successBanner = '<div style="background:rgba(0,184,148,0.1); border:1px solid rgba(0,184,148,0.3); color:#00b894; padding:20px; border-radius:12px; margin-bottom:25px; text-align:center; font-size:16px; font-weight:700;">🎉 Order placed successfully! Thank you for your purchase.</div>';
        }
        
        $totalFmt = number_format($order['total_amount'], 2);
        $safeAddress = htmlspecialchars($order['shipping_address']);
        
        $PAGE_CONTENT = <<<HTML
        <div style="margin-bottom:30px;">
            <a href="/orders.php" style="color:var(--accent); text-decoration:none; font-size:14px; font-weight:600;">← All Orders</a>
        </div>
        
        {$successBanner}
        
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px; flex-wrap:wrap; gap:15px;">
            <div>
                <h1 style="font-family:'Outfit',sans-serif; margin:0;">Order #{$orderId}</h1>
                <p style="color:var(--text-muted); font-size:14px; margin-top:5px;">{$orderDate}</p>
            </div>
            <div style="padding:8px 20px; border-radius:50px; background:rgba(0,0,0,0.2); border:2px solid {$statusColor}; color:{$statusColor}; font-weight:800; font-size:13px; text-transform:uppercase; letter-spacing:1px;">{$statusLabel}</div>
        </div>
        
        <div style="display:grid; grid-template-columns:1fr 350px; gap:25px; align-items:start;">
            <div class="card" style="padding:25px;">
                <h3 style="margin-bottom:15px; color:var(--text-primary);">Items</h3>
                {$itemsHtml}
                <div style="display:flex; justify-content:space-between; padding-top:15px; margin-top:5px; font-size:20px; font-weight:800; color:var(--text-primary);">
                    <span>Total</span><span style="color:var(--accent);">\${$totalFmt}</span>
                </div>
            </div>
            <div class="card" style="padding:25px;">
                <h3 style="margin-bottom:15px; color:var(--text-primary);">Shipping</h3>
                <p style="color:var(--text-secondary); line-height:1.6;">{$safeAddress}</p>
                <div style="margin-top:20px; padding-top:15px; border-top:1px solid var(--glass-border);">
                    <div style="font-size:12px; color:var(--text-muted); font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Customer</div>
                    <div style="color:var(--text-primary); font-weight:600;">{$order['username']}</div>
                </div>
            </div>
        </div>
HTML;
    } else {
        $PAGE_CONTENT = '<div class="card" style="padding:40px; text-align:center;"><h2>Order not found</h2><p style="color:var(--text-secondary);">The order you are looking for does not exist.</p><a href="/orders.php" class="btn" style="margin-top:20px; display:inline-block;">View All Orders</a></div>';
    }
} else {
    // List all orders for this user
    $ordersResult = $conn->query("SELECT * FROM orders WHERE user_id = {$userId} ORDER BY created_at DESC");
    $orders = $ordersResult ? $ordersResult->fetch_all(MYSQLI_ASSOC) : [];
    
    $ordersHtml = '';
    if (empty($orders)) {
        $ordersHtml = '<div style="text-align:center; padding:60px 20px; color:var(--text-secondary);">
            <div style="font-size:64px; margin-bottom:20px;">📦</div>
            <h3 style="margin-bottom:10px; color:var(--text-primary);">No orders yet</h3>
            <p>Start shopping to see your orders here.</p>
            <a href="/products.php" class="btn" style="margin-top:20px; display:inline-block;">Browse Products</a>
        </div>';
    } else {
        foreach ($orders as $o) {
            $statusColor = match($o['status']) {
                'confirmed' => '#00b894',
                'shipped' => '#0984e3',
                'delivered' => '#6c5ce7',
                default => '#fdcb6e'
            };
            $statusLabel = ucfirst($o['status']);
            $totalFmt = number_format($o['total_amount'], 2);
            $dateStr = date('M j, Y', strtotime($o['created_at']));
            
            $ordersHtml .= <<<HTML
            <a href="/orders.php?id={$o['id']}" class="card" style="display:flex; align-items:center; gap:20px; padding:20px; margin-bottom:12px; text-decoration:none; transition:transform 0.2s, box-shadow 0.2s; cursor:pointer;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
                <div style="font-size:28px;">📦</div>
                <div style="flex:1;">
                    <div style="font-weight:700; color:var(--text-primary); font-size:16px;">Order #{$o['id']}</div>
                    <div style="font-size:13px; color:var(--text-muted); margin-top:3px;">{$dateStr}</div>
                </div>
                <div style="font-weight:700; color:var(--text-primary); font-size:18px; margin-right:15px;">\${$totalFmt}</div>
                <div style="padding:5px 14px; border-radius:50px; background:rgba(0,0,0,0.15); color:{$statusColor}; font-weight:700; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">{$statusLabel}</div>
            </a>
HTML;
        }
    }
    
    $PAGE_CONTENT = <<<HTML
    <div style="margin-bottom:40px;">
        <div class="page-title">
            <span style="font-size:48px;">📦</span>
            <div>
                <h1 style="margin:0; font-family:'Outfit',sans-serif;">My Orders</h1>
                <p style="font-size:14px; color:var(--text-secondary); font-weight:500;">Track and manage your purchases</p>
            </div>
        </div>
    </div>
    
    <div style="max-width:800px;">
        {$ordersHtml}
    </div>
HTML;
}

$conn->close();
include '/app/templates/app_template.php';
?>