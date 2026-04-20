<?php
session_start();
$_SESSION['username'] = 'admin';

$url = isset($_GET['url']) ? $_GET['url'] : '';
$content = '';

if ($url) {
    // VULNERABLE: SSRF - no URL validation
    $content = @file_get_contents($url);
    if ($content === false) {
        $content = "Failed to fetch URL";
    }
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">🖼️ Image Proxy</h1>
    
    <div class="card">
        <div class="card-title">Fetch External Image</div>
        <form method="GET">
            <div class="form-group">
                <label>Image URL</label>
                <input type="text" name="url" value="{$url}" placeholder="https://example.com/image.jpg">
            </div>
            <button type="submit" class="btn">Fetch Image</button>
        </form>
        <div style='margin-top:15px; padding:12px; background:#fff3cd; border-radius:6px; color:#856404; font-size:14px;'>
            💡 <strong>Testing Tip:</strong> Try: <code>http://127.0.0.1:8080</code>, <code>file:///etc/passwd</code>
        </div>
    </div>
    
    {$content && '<div class="card"><div class="card-title">Response</div><pre style="background:#f5f5f5; padding:20px; border-radius:8px; overflow-x:auto; max-height:400px;">' . htmlspecialchars(substr($content, 0, 1000)) . '</pre></div>'}
</div>
HTML;

include '/app/templates/app_template.php';
?>