<?php
session_start();

// Redirect if not logged in
if (!isset($_SESSION['user_id'])) {
    header('Location: /login.php');
    exit;
}

// Fetch stats
$conn = new mysqli('db', 'root', 'password', 'dvwa');
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$totalOrders = $conn->query("SELECT COUNT(*) as count FROM orders")->fetch_assoc()['count'] ?? 0;
$totalRevenue = $conn->query("SELECT SUM(total_price) as revenue FROM orders WHERE status != 'pending'")->fetch_assoc()['revenue'] ?? 0;
$totalCustomers = $conn->query("SELECT COUNT(DISTINCT user_id) as count FROM orders")->fetch_assoc()['count'] ?? 0;
$totalProducts = $conn->query("SELECT COUNT(*) as count FROM products")->fetch_assoc()['count'] ?? 0;

// Fetch recent activity
$recentRows = '';
$result = $conn->query("SELECT o.created_at, u.username AS customer, o.status, o.total_price 
                        FROM orders o 
                        JOIN users u ON o.user_id = u.id 
                        ORDER BY o.created_at DESC LIMIT 5");

if ($result && $result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $statusClass = $row['status'] === 'pending' ? 'warning' : 'success';
        $recentRows .= "<tr>
            <td>" . htmlspecialchars($row['created_at']) . "</td>
            <td>" . htmlspecialchars($row['customer']) . "</td>
            <td><span class='badge badge-{$statusClass}'>" . htmlspecialchars(ucfirst($row['status'])) . "</span></td>
            <td style='color:var(--success); font-weight:700;'>\$" . number_format((float)$row['total_price'], 2) . "</td>
        </tr>";
    }
} else {
    $recentRows = '<tr><td colspan="4" style="text-align:center; padding:40px; color:var(--text-muted);">No recent activity</td></tr>';
}

$conn->close();

$PAGE_CONTENT = <<<HTML
<h1 class="page-title">📊 Dashboard</h1>

<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:20px; margin-bottom:30px;">
    <div class="card" style="text-align:center; border-top:3px solid var(--accent);">
        <div style="font-size:40px; font-weight:800; background:linear-gradient(135deg, var(--accent-light), #8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px;">{$totalOrders}</div>
        <div style="color:var(--text-secondary); font-weight:600; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">Total Orders</div>
    </div>
    <div class="card" style="text-align:center; border-top:3px solid var(--danger);">
        <div style="font-size:40px; font-weight:800; background:linear-gradient(135deg, var(--danger), #ee5a24); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px;">\${$totalRevenue}</div>
        <div style="color:var(--text-secondary); font-weight:600; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">Revenue</div>
    </div>
    <div class="card" style="text-align:center; border-top:3px solid var(--success);">
        <div style="font-size:40px; font-weight:800; background:linear-gradient(135deg, var(--success), #00b894); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px;">{$totalCustomers}</div>
        <div style="color:var(--text-secondary); font-weight:600; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">Customers</div>
    </div>
    <div class="card" style="text-align:center; border-top:3px solid var(--warning);">
        <div style="font-size:40px; font-weight:800; background:linear-gradient(135deg, var(--warning), #e17055); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px;">{$totalProducts}</div>
        <div style="color:var(--text-secondary); font-weight:600; font-size:13px; text-transform:uppercase; letter-spacing:0.5px;">Products</div>
    </div>
</div>

<div class="card">
    <div class="card-title">Recent Activity</div>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Amount</th>
            </tr>
        </thead>
        <tbody>
            {$recentRows}
        </tbody>
    </table>
</div>
HTML;

include '/app/templates/app_template.php';
?>