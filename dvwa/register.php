<?php
session_start();
$username = $_POST['username'] ?? '';
$email = $_POST['email'] ?? '';

// VULNERABLE: SQL Injection in user creation
if ($username !== '') {
    $query = "INSERT INTO users (username, email, role) VALUES ('" . $username . "', '" . $email . "', 'user')";
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <h1 class="page-title">📝 Create Account</h1>
    <div class="card">
        <form method="POST">
            <div class="form-group">
                <label>Username:</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>Email Address:</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">Register</button>
        </form>
    </div>
HTML;
if (isset($query)) {
    $PAGE_CONTENT .= '<div class="card alert alert-info"><p>System Logic: <code>' . htmlspecialchars($query) . '</code></p></div>';
}
$PAGE_CONTENT .= '</div>';
include '/app/templates/app_template.php';
?>