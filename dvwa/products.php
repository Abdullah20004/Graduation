<?php
session_start();
$category = $_GET['category'] ?? '';
$search = $_GET['q'] ?? '';

$conn = new mysqli('db', 'root', 'password', 'dvwa');
$productCards = '';
$query = "SELECT * FROM products";

if ($conn->connect_error) {
    $productCards = '<p style="color:var(--text-secondary);">Database connection failed.</p>';
} else {
    // VULNERABLE: Direct concatenation for SQLi training
    $where_clauses = [];
    if ($category !== '') {
        $where_clauses[] = "category = '" . $category . "'";
    }
    if ($search !== '') {
        $where_clauses[] = "(name LIKE '%" . $search . "%' OR description LIKE '%" . $search . "%')";
    }
    
    if (!empty($where_clauses)) {
        $query .= " WHERE " . implode(" AND ", $where_clauses);
    }
    
    $productsResult = $conn->query($query);
    if ($productsResult) {
        $products = $productsResult->fetch_all(MYSQLI_ASSOC);
        foreach ($products as $product) {
            $imageUrl = !empty($product['image_url']) ? $product['image_url'] : 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=400&h=300&fit=crop';
            $productCards .= <<<HTML
            <div class="product-card">
                <div class="image-wrapper">
                    <img class="product-image" src="{$imageUrl}" alt="{$product['name']}">
                </div>
                <div class="product-body">
                    <div style="font-size: 11px; color: var(--accent-light); font-weight: 800; text-transform: uppercase; margin-bottom: 5px;">{$product['category']}</div>
                    <h3 style="margin-bottom: 10px;">{$product['name']}</h3>
                    <p class="product-desc">{$product['description']}</p>
                    <div class="product-footer">
                        <span class="product-price">\${$product['price']}</span>
                        <form method="POST" action="/cart.php" style="margin:0;">
                            <input type="hidden" name="action" value="add">
                            <input type="hidden" name="product_id" value="{$product['id']}">
                            <button type="submit" class="btn" style="padding:8px 16px; font-size:12px;">Add to Cart</button>
                        </form>
                    </div>
                </div>
            </div>
HTML;
        }
    }
    if (empty($productCards)) {
        $productCards = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">No products found in this category.</div>';
    }
    $conn->close();
}

$safeSearch = htmlspecialchars($search, ENT_QUOTES, 'UTF-8');
$cat_all = $category == '' ? 'selected' : '';
$cat_laptops = $category == 'Laptops' ? 'selected' : '';
$cat_phones = $category == 'Phones' ? 'selected' : '';
$cat_audio = $category == 'Audio' ? 'selected' : '';
$cat_acc = $category == 'Accessories' ? 'selected' : '';
$cat_monitors = $category == 'Monitors' ? 'selected' : '';
$cat_gaming = $category == 'Gaming' ? 'selected' : '';

$PAGE_CONTENT = <<<HTML
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:40px; gap:20px; flex-wrap:wrap;">
        <div>
            <h1 class="page-title" style="margin-bottom:10px;">🛍️ Product Catalog</h1>
            <p style="color:var(--text-secondary);">Explore our range of high-performance electronics.</p>
        </div>
        
        <div class="card" style="margin-bottom:0; padding:15px 25px; min-width:450px;">
            <form method="GET" style="display:flex; gap:15px; align-items:center;">
                <div class="form-group" style="margin-bottom:0; flex-grow:2;">
                    <input type="text" name="q" value="{$safeSearch}" placeholder="Search products..." style="padding:10px 15px;">
                </div>
                <div class="form-group" style="margin-bottom:0; flex-grow:1;">
                    <select name="category" style="padding:10px 15px; background:rgba(0,0,0,0.2); border:1px solid var(--glass-border); color:var(--text-primary); border-radius:var(--radius-sm);">
                        <option value="" {$cat_all}>All Categories</option>
                        <option value="Laptops" {$cat_laptops}>Laptops</option>
                        <option value="Phones" {$cat_phones}>Phones</option>
                        <option value="Audio" {$cat_audio}>Audio</option>
                        <option value="Accessories" {$cat_acc}>Accessories</option>
                        <option value="Monitors" {$cat_monitors}>Monitors</option>
                        <option value="Gaming" {$cat_gaming}>Gaming</option>
                    </select>
                </div>
                <button class="btn" style="padding:10px 20px;">Search</button>
            </form>
        </div>
    </div>

    <div class="product-grid">
        {$productCards}
    </div>


HTML;

include '/app/templates/app_template.php';
?>