<?php
session_start();
$_SESSION['username'] = 'admin';

$uploaded = false;
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['image'])) {
    $filename = $_FILES['image']['name'];
    
    // VULNERABLE: No file type validation, allows code execution
    $target = "/tmp/" . basename($filename);
    
    if (move_uploaded_file($_FILES['image']['tmp_name'], $target)) {
        $uploaded = true;
    } else {
        $error = "Upload failed";
    }
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">📤 Image Upload</h1>
    
    {$uploaded && '<div class="alert alert-success">✅ File uploaded successfully!</div>'}
    {$error && '<div class="alert alert-error">❌ ' . $error . '</div>'}
    
    <div class="card">
        <div class="card-title">Upload Product Image</div>
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label>Select Image</label>
                <input type="file" name="image" accept="image/*">
            </div>
            <button type="submit" class="btn">Upload</button>
        </form>
        <div style='margin-top:15px; padding:12px; background:#fff3cd; border-radius:6px; color:#856404; font-size:14px;'>
            💡 <strong>Testing Tip:</strong> Try uploading a PHP file with <code>&lt;?php system(\$_GET['cmd']); ?&gt;</code>
        </div>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>