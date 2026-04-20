<?php
session_start();

// Temporary forced login for testing
if (!isset($_SESSION['user_id'])) {
    $_SESSION['username'] = 'admin';
}

$message = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // VULNERABLE: No CSRF protection
    if (!empty($_POST['new_password'])) {
        $message = "Password changed successfully! (Demo only - no real change)";
    }
}

// Pre-build message (safe heredoc)
$messageHtml = $message !== ''
    ? '<div class="alert alert-success" style="margin-bottom:20px; padding:15px; background:#efe; border:1px solid #cfc; border-radius:8px;">
           ✅ ' . htmlspecialchars($message, ENT_QUOTES, 'UTF-8') . '
       </div>'
    : '';

$testingTip = "💡 <strong>Testing Tip:</strong> This form has no CSRF protection. 
    Craft a malicious page on another domain that auto-submits this form when visited.";

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker" title="CSRF Vulnerability Present"></div>
    <h1 class="page-title">⚙️ Account Settings</h1>
    
    {$messageHtml}
    
    <div class="card">
        <div class="card-title">Change Password</div>
        <form method="POST">
            <div class="form-group">
                <label>Current Password</label>
                <input type="password" name="current_password" required>
            </div>
            <div class="form-group">
                <label>New Password</label>
                <input type="password" name="new_password" required>
            </div>
            <div class="form-group">
                <label>Confirm New Password</label>
                <input type="password" name="confirm_password" required>
            </div>
            <button type="submit" class="btn">Update Password</button>
        </form>
        
        <div style="margin-top:20px; padding:15px; background:#fff3cd; border-radius:8px; color:#856404;">
            {$testingTip}
        </div>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>