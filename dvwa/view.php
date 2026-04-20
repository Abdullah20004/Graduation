<?php
session_start();
$_SESSION['username'] = 'admin';

$file = isset($_GET['file']) ? $_GET['file'] : 'welcome.txt';
$content = '';

// VULNERABLE: LFI - no path validation
if (file_exists($file)) {
    $content = file_get_contents($file);
} else {
    $content = "File not found: " . htmlspecialchars($file);
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">📄 Document Viewer</h1>
    
    <div class="card">
        <form method="GET">
            <div class="form-group">
                <label>File Path</label>
                <input type="text" name="file" value="{$file}" placeholder="/path/to/file">
            </div>
            <button type="submit" class="btn">Load File</button>
        </form>
        <div style='margin-top:15px; padding:12px; background:#e7f3ff; border-radius:6px; color:#004085; font-size:14px;'>
            💡 <strong>Testing Tip:</strong> Try: <code>/etc/passwd</code>, <code>../../../../etc/passwd</code>, <code>../config/database.php</code>
        </div>
    </div>
    
    <div class="card">
        <div class="card-title">File Contents</div>
        <pre style='background:#f5f5f5; padding:20px; border-radius:8px; overflow-x:auto; max-height:400px;'>{$content}</pre>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>