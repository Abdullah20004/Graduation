<?php
session_start();

// Basic admin check
if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'admin') {
    header('Location: /admin_login.php');
    exit;
}

$conn = new mysqli('db', 'root', 'password', 'dvwa');
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Fetch stats
$userCount = $conn->query("SELECT COUNT(*) as count FROM users")->fetch_assoc()['count'];
$orderCount = $conn->query("SELECT COUNT(*) as count FROM orders")->fetch_assoc()['count'];
$revenue = $conn->query("SELECT SUM(total_amount) as total FROM orders")->fetch_assoc()['total'] ?? 0;
$productCount = $conn->query("SELECT COUNT(*) as count FROM products")->fetch_assoc()['count'];

$PAGE_CONTENT = <<<HTML
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
    <h1 class="page-title" style="margin: 0;">🛡️ Admin Dashboard</h1>
    <div style="color: var(--text-secondary); font-size: 14px;">Welcome back, <strong>Admin</strong></div>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;">
    <div class="card" style="padding: 25px; text-align: center;">
        <div style="font-size: 32px; margin-bottom: 10px;">👥</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--primary);">{$userCount}</div>
        <div style="color: var(--text-secondary); font-size: 14px;">Total Users</div>
    </div>
    <div class="card" style="padding: 25px; text-align: center;">
        <div style="font-size: 32px; margin-bottom: 10px;">🛒</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--primary);">{$orderCount}</div>
        <div style="color: var(--text-secondary); font-size: 14px;">Total Orders</div>
    </div>
    <div class="card" style="padding: 25px; text-align: center;">
        <div style="font-size: 32px; margin-bottom: 10px;">💰</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--primary);">\${$revenue}</div>
        <div style="color: var(--text-secondary); font-size: 14px;">Total Revenue</div>
    </div>
    <div class="card" style="padding: 25px; text-align: center;">
        <div style="font-size: 32px; margin-bottom: 10px;">📦</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--primary);">{$productCount}</div>
        <div style="color: var(--text-secondary); font-size: 14px;">Products in Catalog</div>
    </div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; flex-wrap: wrap;">
    <div class="card" style="padding: 30px;">
        <h3>Quick Actions</h3>
        <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 20px;">
            <a href="/users.php" class="btn" style="text-align: center;">Manage Users</a>
            <a href="/orders.php" class="btn" style="background: transparent; border: 1px solid var(--primary); color: var(--primary); text-align: center;">View All Orders</a>
            <a href="/products.php" class="btn" style="background: transparent; border: 1px solid var(--border-color); color: var(--text-primary); text-align: center;">Edit Catalog</a>
        </div>
    </div>
    
    <div class="card" style="padding: 30px;">
        <h3>System Status</h3>
        <div style="margin-top: 20px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px;">
                <span>Database Connection</span>
                <span style="color: #00b894; font-weight: 600;">ACTIVE</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px;">
                <span>Storage Usage</span>
                <span>12% of 50GB</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px;">
                <span>Server Load</span>
                <span>0.15 ms</span>
            </div>
            <div style="margin-top: 20px; padding: 10px; background: rgba(9, 132, 227, 0.05); border-radius: 6px; font-size: 12px; color: #0984e3; text-align: center;">
                🛡️ HackGuard™ Firewall is protecting the system.
            </div>
        </div>
    </div>
</div>
HTML;

$conn->close();
include '/app/templates/app_template.php';
?>
