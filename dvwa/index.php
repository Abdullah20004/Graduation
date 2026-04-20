<?php
session_start();

// Fetch featured products (even for guests)
$conn = new mysqli('db', 'root', 'password', 'dvwa');
if ($conn->connect_error) {
    $productCards = '<p style="color:var(--text-secondary);">Products temporarily unavailable.</p>';
    $productCount = 0;
} else {
    $productsResult = $conn->query("SELECT * FROM products ORDER BY rating DESC LIMIT 6");
    $products = $productsResult->fetch_all(MYSQLI_ASSOC);
    $productCount = $conn->query("SELECT COUNT(*) as c FROM products")->fetch_assoc()['c'] ?? 0;
    $conn->close();

    $productCards = '';
    foreach ($products as $product) {
        $imageUrl = !empty($product['image_url']) ? $product['image_url'] : 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=400&h=300&fit=crop';
        $rating = $product['rating'] ?? 4.0;
        $fullStars = floor($rating);
        $stars = str_repeat('★', $fullStars) . str_repeat('☆', 5 - $fullStars);

        $productCards .= <<<HTML
        <div class="product-card">
            <div class="image-wrapper">
                <img class="product-image" src="{$imageUrl}" alt="{$product['name']}" loading="lazy">
            </div>
            <div class="product-body">
                <h3>{$product['name']}</h3>
                <p class="product-desc">{$product['description']}</p>
                <div class="product-meta">
                    <span class="stars">{$stars}</span>
                    <span class="rating-num">{$rating}</span>
                </div>
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <span class="product-price">\${$product['price']}</span>
                    <a href="/products.php" class="btn" style="text-decoration:none; padding:10px 20px; font-size:13px;">View</a>
                </div>
            </div>
        </div>
HTML;
    }
    if (empty($productCards)) {
        $productCards = '<p style="color:var(--text-secondary);">No products available yet.</p>';
    }
}

// Safe username
$username = htmlspecialchars($_SESSION['username'] ?? 'Visitor', ENT_QUOTES, 'UTF-8');

// Build login button conditionally
$loginButton = '';
if (!isset($_SESSION['user_id'])) {
    $loginButton = '<a href="/login.php" class="btn" style="display:inline-block; margin-top:20px; padding:14px 36px; font-size:16px;">Login to Start Shopping</a>';
}

$PAGE_CONTENT = <<<HTML
<div style="padding-top: 40px;">
    <!-- Hero Section -->
    <div style="text-align:center; padding: 40px 0 80px;">
        <div style="display: inline-block; padding: 6px 16px; background: rgba(124, 77, 255, 0.1); border: 1px solid rgba(124, 77, 255, 0.2); border-radius: 50px; color: var(--accent); font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 24px;">
            The Future of Electronics
        </div>
        <h1 style="font-size: clamp(40px, 8vw, 72px); line-height: 1.1; font-weight: 800; font-family: 'Outfit', sans-serif; margin-bottom: 24px; letter-spacing: -2px;">
            Shop Smarter, <br>
            <span style="background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Secure the Future.</span>
        </h1>
        <p style="font-size: 18px; color: var(--text-secondary); max-width: 650px; margin: 0 auto 40px; line-height: 1.6;">
            Welcome back, <span style="color: var(--text-primary); font-weight: 700;">{$username}</span>. SecureShop is your gateway to premium gadgets and a hands-on cybersecurity learning experience.
        </p>
        <div style="display: flex; gap: 16px; justify-content: center;">
            <a href="/products.php" class="btn" style="padding: 16px 40px; font-size: 16px;">Browse Collection</a>
            {$loginButton}
        </div>
    </div>

    <!-- Features -->
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 80px;">
        <div class="card" style="text-align: center; border-bottom: 3px solid var(--accent);">
            <div style="font-size: 32px; margin-bottom: 15px;">🚀</div>
            <h4 style="margin-bottom: 8px;">Fast Delivery</h4>
            <p style="font-size: 13px; color: var(--text-secondary);">Free shipping on all orders over $99 in the continental US.</p>
        </div>
        <div class="card" style="text-align: center; border-bottom: 3px solid var(--success);">
            <div style="font-size: 32px; margin-bottom: 15px;">🛡️</div>
            <h4 style="margin-bottom: 8px;">Secure Payments</h4>
            <p style="font-size: 13px; color: var(--text-secondary);">Military-grade encryption for every transaction you make.</p>
        </div>
        <div class="card" style="text-align: center; border-bottom: 3px solid var(--warning);">
            <div style="font-size: 32px; margin-bottom: 15px;">💎</div>
            <h4 style="margin-bottom: 8px;">Quality Gear</h4>
            <p style="font-size: 13px; color: var(--text-secondary);">Curated selection of top-tier electronics from global brands.</p>
        </div>
    </div>

    <!-- Featured Products -->
    <div style="margin-bottom: 40px; display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
            <h3 style="font-size: 28px; font-family: 'Outfit', sans-serif;">Featured Products</h3>
            <p style="color: var(--text-secondary); font-size: 14px;">Our most popular items this week.</p>
        </div>
        <a href="/products.php" style="color: var(--accent); font-weight: 700; text-decoration: none; font-size: 14px;">View All &rarr;</a>
    </div>

    <div class="product-grid">
        {$productCards}
    </div>

    <!-- Training Notice -->
    <!-- <div class="card" style="margin-top: 100px; padding: 40px; background: rgba(0,0,0,0.4); border: 2px dashed var(--glass-border); position: relative; overflow: hidden;">
        <div style="position: absolute; top: -20px; right: -20px; font-size: 120px; opacity: 0.05; pointer-events: none;">🎯</div>
        <div style="max-width: 600px;">
            <h3 style="margin-bottom: 16px; color: var(--accent);">Target Practice Environment</h3>
            <p style="font-size: 15px; line-height: 1.7; color: var(--text-secondary); margin-bottom: 24px;">
                SecureShop isn't just a store—it's a <strong>Cybersecurity Training Ground</strong>. 
                Discover hidden vulnerabilities in the code, practice your penetration testing skills, and learn how to build truly secure applications.
            </p>
            <div style="display: flex; gap: 12px;">
                <span class="badge badge-success">SQL Injection</span>
                <span class="badge badge-success" style="background: rgba(124, 77, 255, 0.1); color: #7c4dff;">XSS Ready</span>
                <span class="badge badge-success" style="background: rgba(255, 171, 64, 0.1); color: #ffab40;">Active IDOR</span>
            </div>
        </div>
    </div> -->
</div>
HTML;

include '/app/templates/app_template.php';
?>