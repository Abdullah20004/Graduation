<?php
session_start();
$message = $_POST['message'] ?? '';
$tickets = $_SESSION['tickets'] ?? [];

if ($message) {
    // VULNERABLE: Stored XSS
    $tickets[] = ['msg' => $message];
    $_SESSION['tickets'] = $tickets;
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">🎧 Customer Support</h1>
    <div class="card">
        <form method="POST">
            <label>Describe your issue:</label>
            <textarea name="message" rows="4"></textarea>
            <button class="btn">Submit Ticket</button>
        </form>
    </div>
    <div class="card"><div class="card-title">Your Tickets</div>
HTML;
foreach ($tickets as $t) {
    $PAGE_CONTENT .= "<div style='padding:10px; border-bottom:1px solid #eee;'>{$t['msg']}</div>";
}
$PAGE_CONTENT .= '</div></div>';
include '/app/templates/app_template.php';
?>