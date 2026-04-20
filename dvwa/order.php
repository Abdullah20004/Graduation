<?php
session_start();
$_SESSION['username'] = 'admin';

$orderId = isset($_GET['id']) ? $_GET['id'] : '1001';

// VULNERABLE: IDOR - no ownership check
$orders = [
    '1001' => ['customer' => 'John Doe', 'total' => '$149.99', 'items' => 'Laptop Case, Mouse'],
    '1002' => ['customer' => 'Jane Smith', 'total' => '$899.99', 'items' => 'Tablet Pro'],
    '1003' => ['customer' => 'Bob Johnson', 'total' => '$49.99', 'items' => 'USB Cable'],
];

$order = $orders[$orderId] ?? null;

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">📦 Order Details</h1>
    
    <div class="card">
        <form method="GET">
            <div class="form-group">
                <label>Order ID</label>
                <input type="text" name="id" value="{$orderId}" placeholder="Enter Order ID">
            </div>
            <button type="submit" class="btn">View Order</button>
        </form>
        <div style='margin-top:15px; padding:12px; background:#e7f3ff; border-radius:6px; color:#004085; font-size:14px;'>
            💡 <strong>Testing Tip:</strong> Try different order IDs: 1001, 1002, 1003
        </div>
    </div>
HTML;

if ($order) {
    $PAGE_CONTENT .= <<<HTML
    <div class="card">
        <div class="card-title">Order #{$orderId}</div>
        <table>
            <tr><th>Customer:</th><td>{$order['customer']}</td></tr>
            <tr><th>Total:</th><td><strong>{$order['total']}</strong></td></tr>
            <tr><th>Items:</th><td>{$order['items']}</td></tr>
            <tr><th>Status:</th><td><span class='badge badge-success'>Delivered</span></td></tr>
        </table>
    </div>
HTML;
} else {
    $PAGE_CONTENT .= '<div class="alert alert-error">Order not found</div>';
}

$PAGE_CONTENT .= '</div>';

include '/app/templates/app_template.php';
?>