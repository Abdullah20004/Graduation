<?php
session_start();
$log_filter = $_GET['filter'] ?? '';

// VULNERABLE: Direct concatenation
if ($log_filter !== '') {
    $query = "SELECT * FROM admin_logs WHERE action LIKE '%" . $log_filter . "%'";
}

$PAGE_CONTENT = <<<HTML
    <h1 class="page-title">⚙️ Admin Dashboard</h1>
    <div class="card">
        <form method="GET">
            <label>Search Logs:</label>
            <input type="text" name="filter" value="">
            <button class="btn">Search</button>
        </form>
    </div>
HTML;
if (isset($query)) {
    $PAGE_CONTENT .= '<div class="card"><p>DB Query: <code>' . htmlspecialchars($query) . '</code></p></div>';
}
$PAGE_CONTENT .= '</div>';
include '/app/templates/app_template.php';
?>