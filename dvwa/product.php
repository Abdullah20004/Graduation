<?php
session_start();

// Redirect if not logged in
if (!isset($_SESSION['user_id'])) {
    header('Location: /login.php');
    exit;
}

$conn = new mysqli('db', 'root', 'password', 'dvwa');
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// VULNERABLE: SQL Injection - no prepared statement or escaping
$productId = isset($_GET['id']) ? $_GET['id'] : '1';
$query = "SELECT * FROM products WHERE id = " . $productId;
$result = $conn->query($query);

if ($result && $result->num_rows > 0) {
    $product = $result->fetch_assoc();
    $imageUrl = !empty($product['image_url']) ? $product['image_url'] : 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=800';
    $rating = $product['rating'] ?? 4.0;
    $fullStars = floor($rating);
    $stars = str_repeat('★', $fullStars) . str_repeat('☆', 5 - $fullStars);
    
    $PAGE_CONTENT = <<<HTML
    <div style="margin-bottom: 20px;">
        <a href="/products.php" style="color: var(--primary); text-decoration: none; font-size: 14px;">← Back to Products</a>
    </div>

    <div class="card" style="display: flex; flex-direction: row; gap: 40px; padding: 40px; align-items: flex-start; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px;">
            <div class="image-wrapper" style="border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <img src="{$imageUrl}" alt="{$product['name']}" style="width: 100%; height: auto; display: block; transition: transform 0.3s ease;">
            </div>
        </div>
        
        <div style="flex: 1; min-width: 300px;">
            <div class="badge badge-success" style="margin-bottom: 12px; font-size: 12px; background: rgba(0, 184, 148, 0.1); color: #00b894; border: 1px solid rgba(0, 184, 148, 0.2);">{$product['category']}</div>
            <h1 style="font-size: 32px; margin-bottom: 12px; color: var(--text-primary);">{$product['name']}</h1>
            
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 24px;">
                <span style="color: #f1c40f; font-size: 20px;">{$stars}</span>
                <span style="color: var(--text-secondary); font-size: 14px;">({$rating} rating)</span>
                <span style="color: #636e72; font-size: 14px;">• 120+ reviews</span>
            </div>
            
            <div style="font-size: 28px; font-weight: 700; color: var(--primary); margin-bottom: 24px;">\${$product['price']}</div>
            
            <div style="margin-bottom: 32px; line-height: 1.6; color: var(--text-secondary);">
                <h3 style="font-size: 18px; margin-bottom: 12px; color: var(--text-primary);">Product Description</h3>
                <p>{$product['description']}</p>
                <p style="margin-top: 15px;">Experience top-tier performance and reliability with the {$product['name']}. Designed for those who demand excellence in every detail.</p>
            </div>
            
            <div style="display: flex; gap: 15px;">
                <form action="/cart.php" method="POST" style="flex: 1;">
                    <input type="hidden" name="action" value="add">
                    <input type="hidden" name="product_id" value="{$product['id']}">
                    <button type="submit" class="btn" style="width: 100%; padding: 15px; font-size: 16px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                        <span>🛒</span> Add to Cart
                    </button>
                </form>
                <button class="btn" style="background: transparent; border: 1px solid var(--border-color); color: var(--text-primary); padding: 15px;">
                    ♡
                </button>
            </div>
            
            <div style="margin-top: 24px; padding: 15px; background: rgba(0,0,0,0.02); border-radius: 8px; border: 1px dashed var(--border-color);">
                <div style="font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">🚚</span> 
                    <span>Fast delivery within 2-3 business days</span>
                </div>
            </div>
        </div>
    </div>
    
    <div style="margin-top: 40px;">
        <h2 style="margin-bottom: 20px;">Customer Reviews</h2>
        <div class="card" style="padding: 24px;">
            <div style="color: var(--text-secondary); text-align: center; padding: 40px;">
                <p>No verified reviews yet. Be the first to review this product!</p>
                <a href="/reviews.php?product_id={$product['id']}" class="btn" style="margin-top: 15px; display: inline-block;">Write a Review</a>
            </div>
        </div>
    </div>
HTML;
} else {
    $PAGE_CONTENT = '<div class="alert alert-error">Product not found or invalid ID.</div>';
    if ($conn->error) {
        $PAGE_CONTENT .= '<div class="card" style="margin-top: 20px; background: #fff5f5; border: 1px solid #feb2b2; color: #c53030;">
            <strong>SQL Error:</strong> ' . htmlspecialchars($conn->error) . '<br>
            <strong>Query:</strong> ' . htmlspecialchars($query) . '
        </div>';
    }
}

$conn->close();
include '/app/templates/app_template.php';
?>
