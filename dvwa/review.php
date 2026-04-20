<?php
session_start();
$_SESSION['username'] = 'admin';

$review = isset($_POST['review']) ? $_POST['review'] : '';
$reviews = isset($_SESSION['reviews']) ? $_SESSION['reviews'] : [];

if ($review) {
    // VULNERABLE: Stored XSS - no sanitization
    $reviews[] = ['author' => $_SESSION['username'], 'text' => $review, 'time' => date('Y-m-d H:i')];
    $_SESSION['reviews'] = $reviews;
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">⭐ Product Reviews</h1>
    
    <div class="card">
        <div class="card-title">Write a Review</div>
        <form method="POST">
            <div class="form-group">
                <label>Your Review</label>
                <textarea name="review" rows="4" placeholder="Share your experience..."></textarea>
            </div>
            <button type="submit" class="btn">Submit Review</button>
        </form>
        <div style='margin-top:15px; padding:12px; background:#fff3cd; border-radius:6px; color:#856404; font-size:14px;'>
            💡 <strong>Testing Tip:</strong> Try: <code>&lt;script&gt;alert('XSS')&lt;/script&gt;</code>, <code>&lt;img src=x onerror=alert(1)&gt;</code>
        </div>
    </div>
    
    <div class="card">
        <div class="card-title">Recent Reviews</div>
HTML;

foreach ($reviews as $r) {
    // VULNERABLE: Output without escaping
    $PAGE_CONTENT .= "<div style='padding:15px; background:white; border-radius:8px; margin-bottom:10px; border-left:4px solid #667eea;'>
        <strong>{$r['author']}</strong> <span style='color:#888; font-size:13px;'>• {$r['time']}</span>
        <p style='margin-top:8px;'>{$r['text']}</p>
    </div>";
}

$PAGE_CONTENT .= <<<HTML
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>