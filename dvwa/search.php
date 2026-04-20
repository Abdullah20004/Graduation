<?php
session_start();

$searchQuery = $_GET['q'] ?? '';
$results = [];

$conn = new mysqli('db', 'root', 'password', 'dvwa');

if ($searchQuery !== '' && !$conn->connect_error) {
    // VULNERABLE: Direct concatenation → SQL Injection possible
    $query = "SELECT * FROM products WHERE name LIKE '%" . $searchQuery . "%' OR description LIKE '%" . $searchQuery . "%'";
    $res = $conn->query($query);
    if ($res) {
        $results = $res->fetch_all(MYSQLI_ASSOC);
    }
}

$searchInputValue = htmlspecialchars($searchQuery, ENT_QUOTES, 'UTF-8');

// Build result cards
$resultCards = '';
if ($searchQuery === '') {
    $resultCards = '<div style="text-align:center; padding:60px 20px; color:var(--text-secondary);">
        <div style="font-size:64px; margin-bottom:20px;">🔍</div>
        <h3 style="margin-bottom:10px; color:var(--text-primary);">Search our catalog</h3>
        <p>Enter a keyword above to find products.</p>
    </div>';
} elseif (empty($results)) {
    $resultCards = '<div style="text-align:center; padding:60px 20px; color:var(--text-secondary);">
        <div style="font-size:64px; margin-bottom:20px;">😕</div>
        <h3 style="margin-bottom:10px; color:var(--text-primary);">No results found</h3>
        <p>Try a different search term.</p>
    </div>';
} else {
    $count = count($results);
    $resultCards .= "<div style='margin-bottom:20px; font-size:14px; color:var(--text-secondary);'>{$count} products found for <strong style='color:var(--accent);'>\"{$searchInputValue}\"</strong></div>";
    $resultCards .= '<div class="product-grid">';
    foreach ($results as $product) {
        $imageUrl = !empty($product['image_url']) ? $product['image_url'] : 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=400&h=300&fit=crop';
        $rating = $product['rating'] ?? 4.0;
        $fullStars = floor($rating);
        $stars = str_repeat('★', $fullStars) . str_repeat('☆', 5 - $fullStars);
        
        $resultCards .= <<<HTML
        <div class="product-card">
            <div class="image-wrapper">
                <img class="product-image" src="{$imageUrl}" alt="{$product['name']}" loading="lazy">
            </div>
            <div class="product-body">
                <div style="font-size:11px; color:var(--accent-light); font-weight:800; text-transform:uppercase; margin-bottom:5px;">{$product['category']}</div>
                <h3 style="margin-bottom:8px;">{$product['name']}</h3>
                <p class="product-desc">{$product['description']}</p>
                <div class="product-meta">
                    <span class="stars">{$stars}</span>
                    <span class="rating-num">{$rating}</span>
                </div>
                <div class="product-footer">
                    <span class="product-price">\${$product['price']}</span>
                    <a href="/product.php?id={$product['id']}" class="btn" style="padding:8px 16px; font-size:12px; text-decoration:none;">View</a>
                </div>
            </div>
        </div>
HTML;
    }
    $resultCards .= '</div>';
}

$PAGE_CONTENT = <<<HTML
    <div style="margin-bottom:40px;">
        <div class="page-title">
            <span style="font-size:48px;">🔍</span>
            <div>
                <h1 style="margin:0; font-family:'Outfit',sans-serif;">Product Search</h1>
                <p style="font-size:14px; color:var(--text-secondary); font-weight:500;">Find exactly what you need</p>
            </div>
        </div>
    </div>

    <div class="card" style="padding:30px; margin-bottom:30px;">
        <form method="GET" action="/search.php" style="display:flex; gap:15px; align-items:flex-end;">
            <div class="form-group" style="flex:1; margin-bottom:0;">
                <label>Search Query</label>
                <input type="text" name="q" value="{$searchInputValue}" placeholder="e.g. MacBook, headphones, gaming..." autofocus>
            </div>
            <button type="submit" class="btn" style="padding:12px 30px; white-space:nowrap;">
                <span>Search</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </button>
        </form>
    </div>

    {$resultCards}
HTML;

if (!empty($conn) && !$conn->connect_error) $conn->close();
include '/app/templates/app_template.php';
?>