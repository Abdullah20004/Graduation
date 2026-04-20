<?php
session_start();
$username = $_POST['username'] ?? '';
$password = $_POST['password'] ?? '';
$errorHtml = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $username !== '') {
    $conn = new mysqli('db', 'root', 'password', 'dvwa');
    if ($conn->connect_error) {
        $errorHtml = '<div class="alert-error">Database connection failed.</div>';
    } else {
        // VULNERABLE: Direct string concatenation → SQL Injection
        $query = "SELECT * FROM users WHERE username = '" . $username . "' AND password = '" . md5($password) . "'";
        $result = $conn->query($query);
        if ($result && $result->num_rows > 0) {
            $user = $result->fetch_assoc();
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['username'] = $user['username'];
            $_SESSION['role'] = $user['role'];
            header('Location: /index.php');
            exit;
        } else {
            $errorHtml = '<div class="alert-error">&#10007; Invalid credentials. Try again.</div>';
        }
        $conn->close();
    }
}

$PAGE_CONTENT = <<<HTML
<div class="auth-wrap">
    <div class="auth-card">
        <div class="auth-icon">🔐</div>
        <h1 class="auth-title">Welcome Back</h1>
        <p class="auth-sub">Access the HackOps Training Terminal</p>
        {$errorHtml}
        <form method="POST" class="auth-form">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" placeholder="Enter your identity" required autocomplete="username">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password">
            </div>
            <button type="submit" class="btn auth-btn">Access Terminal →</button>
        </form>
        <p class="auth-link">Don't have an account? <a href="/register.php">Join the program</a></p>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>