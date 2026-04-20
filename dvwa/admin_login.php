<?php
session_start();
$admin_user = $_POST['admin_user'] ?? '';

// VULNERABLE: Direct concatenation
if ($admin_user !== '') {
    $query = "SELECT * FROM admins WHERE username = '" . $admin_user . "' AND password = '...'";
}

$PAGE_CONTENT = <<<HTML
    <h1 class="page-title">🛡️ Admin Portal</h1>
    <div class="card">
        <form method="POST">
            <label>Admin Username:</label>
            <input type="text" name="admin_user" value="">
            <label>Password:</label>
            <input type="password" name="password" value="">
            <button class="btn">Authenticate</button>
        </form>
    </div>
HTML;
if (isset($query)) {
    $PAGE_CONTENT .= '<div class="card"><p>DB Query: <code>' . htmlspecialchars($query) . '</code></p></div>';
}
$PAGE_CONTENT .= '</div>';
include '/app/templates/app_template.php';
?>