<?php
session_start();

// Redirect if not logged in
if (!isset($_SESSION['user_id'])) {
    header('Location: /login.php');
    exit;
}

$PAGE_CONTENT = <<<HTML
<h1 class="page-title">❓ Help Center</h1>

<div class="card">
    <div class="card-title">Frequently Asked Questions</div>
    <div style="gap:20px;">
        <div style="margin-bottom:25px;">
            <h4 style="font-size:18px; margin-bottom:10px; color:#667eea;">How do I track my order?</h4>
            <p style="color:#666; line-height:1.6;">Visit the Orders page and enter your order ID to see the current status and tracking information.</p>
        </div>
        <div style="margin-bottom:25px;">
            <h4 style="font-size:18px; margin-bottom:10px; color:#667eea;">What payment methods do you accept?</h4>
            <p style="color:#666; line-height:1.6;">We accept all major credit cards, PayPal, and bank transfers.</p>
        </div>
        <div style="margin-bottom:25px;">
            <h4 style="font-size:18px; margin-bottom:10px; color:#667eea;">How long does shipping take?</h4>
            <p style="color:#666; line-height:1.6;">Standard shipping takes 3-5 business days. Express shipping is available for next-day delivery.</p>
        </div>
        <div style="margin-bottom:25px;">
            <h4 style="font-size:18px; margin-bottom:10px; color:#667eea;">How to report a security issue?</h4>
            <p style="color:#666; line-height:1.6;">Contact support@secureshop.com. This is a training platform — all vulns are intentional!</p>
        </div>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>