<?php
session_start();
$_SESSION['username'] = 'admin';

$result = '';
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['xml'])) {
    $xml = $_POST['xml'];
    
    // VULNERABLE: XXE - external entities enabled
    libxml_disable_entity_loader(false);
    $dom = new DOMDocument();
    
    if (@$dom->loadXML($xml, LIBXML_NOENT | LIBXML_DTDLOAD)) {
        $result = $dom->textContent;
    } else {
        $error = "Invalid XML";
    }
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">📦 Product Import (XML)</h1>
    
    {$error && '<div class="alert alert-error">' . $error . '</div>'}
    {$result && '<div class="alert alert-success">Parsed: ' . htmlspecialchars($result) . '</div>'}
    
    <div class="card">
        <div class="card-title">Upload Product XML</div>
        <form method="POST">
            <div class="form-group">
                <label>XML Data</label>
                <textarea name="xml" rows="10" placeholder="<?xml version='1.0'?>&#10;<products>&#10;  <product>&#10;    <name>Sample</name>&#10;  </product>&#10;</products>"></textarea>
            </div>
            <button type="submit" class="btn">Parse XML</button>
        </form>
        <div style='margin-top:15px; padding:12px; background:#fff3cd; border-radius:6px; color:#856404; font-size:14px;'>
            💡 <strong>Testing Tip:</strong> Try: <code>&lt;!DOCTYPE foo [&lt;!ENTITY xxe SYSTEM "file:///etc/passwd"&gt;]&gt;&lt;foo&gt;&amp;xxe;&lt;/foo&gt;</code>
        </div>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>