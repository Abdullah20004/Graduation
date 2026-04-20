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

$message = '';
// Handle User Deletion (Simple logic)
if (isset($_GET['delete'])) {
    $uid = $_GET['delete'];
    if ($uid > 1) { // Don't delete admin
        $stmt = $conn->prepare("DELETE FROM users WHERE id = ?");
        $stmt->bind_param("i", $uid);
        $stmt->execute();
        $message = '<div class="alert alert-success">User ID #'.$uid.' has been deleted.</div>';
    }
}

// Fetch all users
$usersResult = $conn->query("SELECT * FROM users ORDER BY created_at DESC");
$userRows = '';
while ($user = $usersResult->fetch_assoc()) {
    $roleBadge = $user['role'] === 'admin' ? '<span class="badge" style="background:#dfe6e9; color:#2d3436;">Admin</span>' : '<span class="badge badge-success">User</span>';
    $userRows .= <<<HTML
    <tr style="border-bottom: 1px solid var(--border-color);">
        <td style="padding: 15px;">#{$user['id']}</td>
        <td><strong>{$user['username']}</strong></td>
        <td>{$user['email']}</td>
        <td>{$roleBadge}</td>
        <td>{$user['created_at']}</td>
        <td style="text-align: right; padding-right: 15px;">
            <button class="btn" style="background: transparent; color: var(--primary); border: 1px solid var(--primary); padding: 5px 12px; font-size: 12px;">Edit</button>
            <a href="?delete={$user['id']}" class="btn" style="background: #ff7675; border-color: #ff7675; padding: 5px 12px; font-size: 12px; margin-left: 5px;" onclick="return confirm('Are you sure?')">Delete</a>
        </td>
    </tr>
HTML;
}

$PAGE_CONTENT = <<<HTML
<div style="margin-bottom: 20px;">
    <a href="/admin.php" style="color: var(--primary); text-decoration: none; font-size: 14px;">← Back to Dashboard</a>
</div>

<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
    <h1 class="page-title" style="margin:0;">👥 User Management</h1>
    <button class="btn">Add New User</button>
</div>

{$message}

<div class="card" style="padding: 0; overflow: hidden;">
    <table style="width: 100%; border-collapse: collapse; text-align: left;">
        <thead style="background: rgba(0,0,0,0.02); border-bottom: 1px solid var(--border-color);">
            <tr>
                <th style="padding: 15px;">ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Joined Date</th>
                <th style="text-align: right; padding-right: 15px;">Actions</th>
            </tr>
        </thead>
        <tbody>
            {$userRows}
        </tbody>
    </table>
</div>

<div style='margin-top:40px; padding:15px; background:rgba(0,0,0,0.02); border-radius:8px; border: 1px dashed var(--border-color); color:var(--text-secondary); font-size:13px; text-align: center;'>
    💡 <strong>Admin Tip:</strong> Ensure that only authorized personnel have access to this management interface.
</div>
HTML;

$conn->close();
include '/app/templates/app_template.php';
?>
