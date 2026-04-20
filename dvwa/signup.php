<?php
session_start();
$error = '';
$username = '';
$email = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $password = $_POST['password'] ?? '';
    $confirm = $_POST['confirm_password'] ?? '';
    
    if (empty($username) || empty($email) || empty($password)) {
        $error = 'All fields are required';
    } elseif ($password !== $confirm) {
        $error = 'Passwords do not match';
    } elseif (strlen($password) < 6) {
        $error = 'Password must be at least 6 characters';
    } else {
        $conn = new mysqli('db', 'root', 'password', 'dvwa');
        
        if ($conn->connect_error) {
            $error = 'Database connection failed. Please try again later.';
        } else {
            $hashed = password_hash($password, PASSWORD_BCRYPT);
            
            $stmt = $conn->prepare("INSERT INTO users (username, email, password) VALUES (?, ?, ?)");
            $stmt->bind_param('sss', $username, $email, $hashed);
            
            try {
                if ($stmt->execute()) {
                    $stmt->close();
                    $conn->close();
                    header('Location: /login.php?registered=1');
                    exit;
                } else {
                    $error = 'Registration failed. Please try again.';
                }
            } catch (mysqli_sql_exception $e) {
                if ($e->getCode() === 1062) {
                    if (stripos($e->getMessage(), 'username') !== false) {
                        $error = 'Username already taken. Please choose another.';
                    } elseif (stripos($e->getMessage(), 'email') !== false) {
                        $error = 'Email already registered. Use a different email.';
                    } else {
                        $error = 'Username or email already exists.';
                    }
                } else {
                    $error = 'An error occurred during registration. Please try again.';
                }
            }
            
            $stmt->close();
            $conn->close();
        }
    }
}

$usernameValue = htmlspecialchars($username ?? '', ENT_QUOTES, 'UTF-8');
$emailValue = htmlspecialchars($email ?? '', ENT_QUOTES, 'UTF-8');

$errorMessage = $error !== ''
    ? '<div class="alert alert-error" style="margin-bottom:20px;">❌ ' . htmlspecialchars($error, ENT_QUOTES, 'UTF-8') . '</div>'
    : '';

$PAGE_CONTENT = <<<HTML
<div style="max-width:420px; margin:50px auto;">
    <div style="text-align:center; margin-bottom:36px;">
        <div style="width:80px; height:80px; margin:0 auto 20px; background:linear-gradient(135deg, var(--success), #00b894); border-radius:20px; display:flex; align-items:center; justify-content:center; font-size:36px; box-shadow:0 12px 40px rgba(0,206,201,0.3);">
            🚀
        </div>
        <h1 style="font-size:28px; font-weight:700; margin-bottom:8px;">Create Account</h1>
        <p style="color:var(--text-secondary); font-size:14px;">Join SecureShop today</p>
    </div>

    {$errorMessage}

    <div class="card" style="padding:32px;">
        <form method="POST">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" value="{$usernameValue}" required autofocus placeholder="Choose a username">
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" value="{$emailValue}" required placeholder="your@email.com">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required placeholder="Min. 6 characters">
            </div>
            <div class="form-group">
                <label>Confirm Password</label>
                <input type="password" name="confirm_password" required placeholder="Repeat your password">
            </div>
            <button type="submit" class="btn" style="width:100%; padding:14px; margin-bottom:16px; font-size:15px;">Create Account</button>
            <div style="text-align:center;">
                <a href="/login.php" style="color:var(--accent-light); text-decoration:none; font-size:14px;">Already have an account? <strong>Login</strong></a>
            </div>
        </form>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>