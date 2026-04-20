<?php
session_start();
$id = $_GET['id'] ?? '1';

$product = null;
$conn = new mysqli('db', 'root', 'password', 'dvwa');
if (!$conn->connect_error) {
    // VULNERABLE: Direct concatenation
    $query = "SELECT * FROM products WHERE id = " . $id;
    $result = $conn->query($query);
    if ($result && $result->num_rows > 0) {
        $product = $result->fetch_assoc();
    }
    $conn->close();
}

if (!$product) {
    $PAGE_CONTENT = "<div class='card'><h2 style='color:var(--error);'>Product Not Found or Invalid ID</h2></div>";
} else {
    $name = htmlspecialchars($product['name'], ENT_QUOTES, 'UTF-8');
    $desc = htmlspecialchars($product['description'], ENT_QUOTES, 'UTF-8');
    $img = htmlspecialchars($product['image_url'], ENT_QUOTES, 'UTF-8');
    $cat = htmlspecialchars($product['category'], ENT_QUOTES, 'UTF-8');
    
    $PAGE_CONTENT = <<<HTML
        <div style="margin-bottom:20px;">
            <a href="/products.php" style="color:var(--primary); text-decoration:none;">← Back to Catalog</a>
        </div>
        
        <div class="card" style="display:flex; gap:30px; flex-wrap:wrap;">
            <div style="flex:1; min-width:300px; height:400px; border-radius:12px; overflow:hidden; background:#1e1e1e;">
                <img src="{\$img}" style="width:100%; height:100%; object-fit:contain;" />
            </div>
            <div style="flex:1; min-width:300px; display:flex; flex-direction:column;">
                <div style="font-size:14px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">{\$cat}</div>
                <h1 style="margin:0 0 15px 0; font-size:32px;">{\$name}</h1>
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:25px;">
                    <span style="font-size:28px; font-weight:bold; color:var(--text-success);">\${\$product['price']}</span>
                    <span style="background:#333; padding:4px 10px; border-radius:4px; font-size:14px;">⭐ {\$product['rating']}/5</span>
                </div>
                
                <h3 style="margin:0 0 10px 0; border-bottom:1px solid var(--border-color); padding-bottom:5px;">Description</h3>
                <p style="color:var(--text-secondary); line-height:1.6; margin-bottom:30px;">{\$desc}</p>
                
                <div style="margin-top:auto; background:rgba(0,0,0,0.2); padding:20px; border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
                    <form method="POST" action="/cart.php?action=add" style="display:flex; gap:15px; align-items:center;">
                        <input type="hidden" name="product_id" value="{\$product['id']}">
                        <div style="display:flex; flex-direction:column; gap:5px;">
                            <label style="font-size:13px; color:var(--text-secondary);">Quantity</label>
                            <input type="number" name="quantity" value="1" min="1" max="{\$product['stock']}" style="width:80px; text-align:center;">
                        </div>
                        <button type="submit" class="btn" style="flex:1; height:45px; font-size:16px; font-weight:bold; margin-top:20px;" {\$product['stock'] <= 0 ? 'disabled' : ''}>
                            {\$product['stock'] > 0 ? 'Add to Cart 🛒' : 'Out of Stock'}
                        </button>
                    </form>
                    <div style="margin-top:10px; font-size:13px; text-align:center; color:var(--text-secondary);">
                        {\$product['stock']} units available in warehouse
                    </div>
                </div>
            </div>
        </div>
HTML;
}

$PAGE_CONTENT .= "</div>";
include '/app/templates/app_template.php';
?>