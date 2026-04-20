<?php
/**
 * Apply Vulnerabilities Script
 * Reads the vulnerability configuration and applies them to the environment
 */
/* apply_vulns.php */
// Handle paths portably
$webRoot = $_SERVER['DOCUMENT_ROOT'] ?: '/var/www/html';
$logDir = '/logs';
if (!is_dir($logDir) && is_dir($webRoot . '/logs')) {
    $logDir = $webRoot . '/logs';
}
$logFile = $logDir . '/vulnerabilities.log';

// Priority: 1. Env, 2. Standard location
$envConfig = getenv('VULNS_JSON_PATH');
$configFile = $envConfig ?: $webRoot . '/config/vulns.json';

// // Ensure template directory exists
// $templateDir = '/app/templates';
// if (!is_dir($templateDir)) {
//     mkdir($templateDir, 0755, true);
// }

// // Create the application template if it doesn't exist
// $templatePath = $templateDir . '/app_template.php';
// if (!file_exists($templatePath)) {
//     $templateContent = file_get_contents(__DIR__ . '/../templates/app_template.php');
//     file_put_contents($templatePath, $templateContent);
// }

function logMessage($message) {
    global $logFile;
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($logFile, "[$timestamp] $message\n", FILE_APPEND);
    echo "$message\n";
}

function createVulnerableFiles($vulns) {
    global $webRoot;
    $vulnerableFiles = [];
    
    foreach ($vulns as $vuln) {
        if (!$vuln['enabled']) continue;
        
        $filename = basename($vuln['location']);
        $filePath = $webRoot . $vuln['location'];
        
        // Create directory if needed
        $dir = dirname($filePath);
        if (!is_dir($dir)) {
            mkdir($dir, 0755, true);
        }
        
        // Generate vulnerable code based on type
        $content = generateVulnerableCode($vuln);
        
        if ($content) {
            // Only write if the file does NOT already exist (preserve custom UI)
            if (!file_exists($filePath)) {
                file_put_contents($filePath, $content);
                logMessage("Created vulnerable file: {$vuln['location']}");
            } else {
                logMessage("Skipped (already exists): {$vuln['location']}");
            }
            $vulnerableFiles[] = $vuln['location'];
        }
    }
    
    return $vulnerableFiles;
}

function generateVulnerableCode($vuln) {
    switch ($vuln['type']) {
        case 'sqli':
            return generateSQLInjection($vuln);
        case 'xss':
            return generateXSS($vuln);
        case 'lfi':
            return generateLFI($vuln);
        case 'rce':
            return generateRCE($vuln);
        case 'misconfig':
            return generateMisconfig($vuln);
        case 'csrf':  // New handling
            return generateCSRF($vuln);
        case 'ssrf':  // New handling
            return generateSSRF($vuln);
        case 'xxe':   // New handling
            return generateXXE($vuln);
        case 'idor':  // New handling
            return generateIDOR($vuln);
        case 'open_redirect':  // New handling
            return generateOpenRedirect($vuln);
        default:
            return null;
    }
}

function generateSQLInjection($vuln) {
    $page_name = basename($vuln['location'], '.php');
    
    if ($page_name === 'search') {
        return <<<'PHP'
<?php
session_start();

$searchQuery = $_GET['q'] ?? '';
$results = [];

// VULNERABLE: Direct concatenation → SQL Injection possible
if ($searchQuery !== '') {
    $conn = new mysqli('db', 'root', 'password', 'dvwa');
    if (!$conn->connect_error) {
        $query = "SELECT * FROM products WHERE name LIKE '%" . $searchQuery . "%' OR description LIKE '%" . $searchQuery . "%'";
        $result = $conn->query($query);
        if ($result) {
            while ($row = $result->fetch_assoc()) {
                $results[] = $row;
            }
        }
        $conn->close();
    }
}

$searchInputValue = htmlspecialchars($searchQuery, ENT_QUOTES, 'UTF-8');

$tableRows = '';
if (empty($results) && $searchQuery !== '') {
    $tableRows = '<tr><td colspan="6" style="text-align:center; padding:30px; color:#999;">No products found for your query.</td></tr>';
} elseif (empty($results)) {
    $tableRows = '<tr><td colspan="6" style="text-align:center; padding:30px; color:#999;">Enter a search query to find products.</td></tr>';
} else {
    foreach ($results as $product) {
        $nameEscaped = htmlspecialchars($product['name'], ENT_QUOTES, 'UTF-8');
        $img = htmlspecialchars($product['image_url'] ?? '', ENT_QUOTES, 'UTF-8');
        $imgTag = $img ? "<img src='{$img}' style='width:50px; height:50px; object-fit:cover; border-radius:5px;'/>" : "📦";
        $tableRows .= "<tr>
            <td>{$product['id']}</td>
            <td>{$imgTag}</td>
            <td style='font-weight:600;'>{$nameEscaped}</td>
            <td style='color:var(--text-success); font-weight:bold;'>\${$product['price']}</td>
            <td>" . ($product['stock'] > 0 ? "<span class='badge badge-success'>{$product['stock']} left</span>" : "<span class='badge' style='background:var(--error);'>Out of stock</span>") . "</td>
            <td><a href='/product_detail.php?id={$product['id']}' class='btn' style='padding:6px 15px; font-size:14px; background:var(--primary);'>View Details</a></td>
        </tr>";
    }
}

$testingTip = "💡 <strong>Testing Tip:</strong> Try payloads like: <code>' OR '1'='1</code>, <code>admin'--</code>, or <code>' UNION SELECT null,null,null,null,null,null,null,null,null--</code>";

$PAGE_CONTENT = <<<HTML
    <h1 class="page-title">🔍 Power Search</h1>
    
    <div class="card" style="margin-bottom:20px;">
        <form method="GET" action="/search.php" style="display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end;">
            <div class="form-group" style="flex:1; margin-bottom:0;">
                <label for="search">Find what you love:</label>
                <input type="text" id="search" name="q" placeholder="Enter product name, category, or description..." value="{$searchInputValue}" style="width:100%; font-size:16px;">
            </div>
            <button type="submit" class="btn" style="min-width:120px; font-size:16px;">Search</button>
        </form>
        <p style="margin-top:10px; font-size:13px; color:var(--text-secondary);">{$testingTip}</p>
    </div>

    <div class="card">
        <div class="card-title">Search Results</div>
        <table style="width:100%; border-collapse:collapse; margin-top:10px;">
            <thead style="border-bottom:2px solid var(--border-color); text-align:left;">
                <tr>
                    <th style="padding:12px;">ID</th>
                    <th style="padding:12px;">Image</th>
                    <th style="padding:12px;">Product</th>
                    <th style="padding:12px;">Price</th>
                    <th style="padding:12px;">Stock</th>
                    <th style="padding:12px;">Action</th>
                </tr>
            </thead>
            <tbody>
                {$tableRows}
            </tbody>
        </table>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>
PHP;
    } elseif ($page_name === 'products') {
        return <<<'PHP'
<?php
session_start();
$category = $_GET['category'] ?? '';
$results = [];

$conn = new mysqli('db', 'root', 'password', 'dvwa');
if (!$conn->connect_error) {
    // VULNERABLE: Direct concatenation
    if ($category !== '') {
        $query = "SELECT * FROM products WHERE category = '" . $category . "' ORDER BY rating DESC";
    } else {
        $query = "SELECT * FROM products ORDER BY rating DESC LIMIT 50";
    }
    
    $result = $conn->query($query);
    if ($result) {
        while ($row = $result->fetch_assoc()) {
            $results[] = $row;
        }
    }
    $conn->close();
}

$gridHtml = '<div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px; margin-top:20px;">';
if (empty($results)) {
    $gridHtml .= '<div class="card" style="grid-column:1/-1; text-align:center;">No products found in this category.</div>';
} else {
    foreach ($results as $p) {
        $name = htmlspecialchars($p['name'], ENT_QUOTES, 'UTF-8');
        $cat = htmlspecialchars($p['category'], ENT_QUOTES, 'UTF-8');
        $img = htmlspecialchars($p['image_url'] ?? '', ENT_QUOTES, 'UTF-8');
        $desc = htmlspecialchars(substr($p['description'] ?? '', 0, 60), ENT_QUOTES, 'UTF-8') . '...';
        
        $gridHtml .= "
        <div class='card' style='display:flex; flex-direction:column; padding:15px; transition:transform 0.2s;'>
            <div style='height:200px; background:#f0f0f0; border-radius:8px; overflow:hidden; margin-bottom:15px;'>
                " . ($img ? "<img src='{$img}' style='width:100%; height:100%; object-fit:cover;'/>" : "") . "
            </div>
            <div style='font-size:12px; color:var(--text-secondary); margin-bottom:5px; text-transform:uppercase; letter-spacing:1px;'>{$cat}</div>
            <h3 style='margin:0 0 10px 0; font-size:18px;'>{$name}</h3>
            <p style='color:var(--text-secondary); font-size:14px; flex-grow:1; margin:0 0 15px 0;'>{$desc}</p>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div style='font-size:20px; font-weight:bold; color:var(--text-success);'>\${$p['price']}</div>
                <a href='/product_detail.php?id={$p['id']}' class='btn' style='padding:8px 16px; background:var(--primary); font-weight:600;'>Buy</a>
            </div>
        </div>";
    }
}
$gridHtml .= '</div>';

$PAGE_CONTENT = <<<HTML
    <h1 class="page-title">🛍️ Product Catalog</h1>
    
    <div style="display:flex; gap:10px; margin-bottom:20px; flex-wrap:wrap;">
        <a href="?category=" class="btn" style="background:#444;">All</a>
        <a href="?category=Laptops" class="btn" style="background:#555;">Laptops</a>
        <a href="?category=Phones" class="btn" style="background:#555;">Phones</a>
        <a href="?category=Audio" class="btn" style="background:#555;">Audio</a>
        <a href="?category=Accessories" class="btn" style="background:#555;">Accessories</a>
        <a href="?category=Components" class="btn" style="background:#555;">Components</a>
        <a href="?category=Monitors" class="btn" style="background:#555;">Monitors</a>
    </div>

    {$gridHtml}
</div>
HTML;

include '/app/templates/app_template.php';
?>
PHP;
    } elseif ($page_name === 'product_detail') {
        return <<<'PHP'
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
                <img src="{$img}" style="width:100%; height:100%; object-fit:contain;" />
            </div>
            <div style="flex:1; min-width:300px; display:flex; flex-direction:column;">
                <div style="font-size:14px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">{$cat}</div>
                <h1 style="margin:0 0 15px 0; font-size:32px;">{$name}</h1>
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:25px;">
                    <span style="font-size:28px; font-weight:bold; color:var(--text-success);">\${$product['price']}</span>
                    <span style="background:#333; padding:4px 10px; border-radius:4px; font-size:14px;">⭐ {$product['rating']}/5</span>
                </div>
                
                <h3 style="margin:0 0 10px 0; border-bottom:1px solid var(--border-color); padding-bottom:5px;">Description</h3>
                <p style="color:var(--text-secondary); line-height:1.6; margin-bottom:30px;">{$desc}</p>
                
                <div style="margin-top:auto; background:rgba(0,0,0,0.2); padding:20px; border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
                    <form method="POST" action="/cart.php?action=add" style="display:flex; gap:15px; align-items:center;">
                        <input type="hidden" name="product_id" value="{$product['id']}">
                        <div style="display:flex; flex-direction:column; gap:5px;">
                            <label style="font-size:13px; color:var(--text-secondary);">Quantity</label>
                            <input type="number" name="quantity" value="1" min="1" max="{$product['stock']}" style="width:80px; text-align:center;">
                        </div>
                        <button type="submit" class="btn" style="flex:1; height:45px; font-size:16px; font-weight:bold; margin-top:20px;" {$product['stock'] <= 0 ? 'disabled' : ''}>
                            {$product['stock'] > 0 ? 'Add to Cart 🛒' : 'Out of Stock'}
                        </button>
                    </form>
                    <div style="margin-top:10px; font-size:13px; text-align:center; color:var(--text-secondary);">
                        {$product['stock']} units available in warehouse
                    </div>
                </div>
            </div>
        </div>
HTML;
}

$PAGE_CONTENT .= "</div>";
include '/app/templates/app_template.php';
?>
PHP;
    } elseif ($page_name === 'cart') {
        return <<<'PHP'
<?php
session_start();

$user_id = $_SESSION['user_id'] ?? 1; // Default to admin for testing if not logged in
$conn = new mysqli('db', 'root', 'password', 'dvwa');
$message = '';

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Handle Add to cart
if (isset($_GET['action']) && $_GET['action'] === 'add' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $p_id = (int)$_POST['product_id'];
    $qty = (int)$_POST['quantity'];
    
    // Check if already in cart
    $check = $conn->query("SELECT id, quantity FROM cart WHERE user_id = {$user_id} AND product_id = {$p_id}");
    if ($check && $check->num_rows > 0) {
        $conn->query("UPDATE cart SET quantity = quantity + {$qty} WHERE user_id = {$user_id} AND product_id = {$p_id}");
    } else {
        $conn->query("INSERT INTO cart (user_id, product_id, quantity) VALUES ({$user_id}, {$p_id}, {$qty})");
    }
    header("Location: /cart.php");
    exit;
}

// Handle Remove from cart
if (isset($_GET['action']) && $_GET['action'] === 'remove') {
    $c_id = (int)$_GET['cart_id'];
    $conn->query("DELETE FROM cart WHERE id = {$c_id} AND user_id = {$user_id}");
    header("Location: /cart.php");
    exit;
}

// Handle Checkout
if (isset($_GET['action']) && $_GET['action'] === 'checkout' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    // VULNERABLE: Direct concatenation for coupons (SQL Injection possibility)
    $discount_code = $_POST['coupon'] ?? '';
    if ($discount_code !== '') {
        $conn->query("SELECT discount FROM coupons WHERE code = '" . $discount_code . "'"); 
        // We just execute it so it can be abused. We don't actually deduct in dummy code.
    }
    
    // Process checkout
    $cart_q = $conn->query("SELECT c.product_id, c.quantity, p.price FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = {$user_id}");
    if ($cart_q && $cart_q->num_rows > 0) {
        $total = 0;
        $items = [];
        while ($r = $cart_q->fetch_assoc()) {
            $total += ($r['price'] * $r['quantity']);
            $items[] = $r;
        }
        
        $conn->query("INSERT INTO orders (user_id, total_amount, shipping_address) VALUES ({$user_id}, {$total}, '123 Fake Street')");
        $order_id = $conn->insert_id;
        
        foreach ($items as $itm) {
            $conn->query("INSERT INTO order_items (order_id, product_id, price, quantity) VALUES ({$order_id}, {$itm['product_id']}, {$itm['price']}, {$itm['quantity']})");
        }
        
        $conn->query("DELETE FROM cart WHERE user_id = {$user_id}");
        $message = "✅ Order #{$order_id} placed successfully!";
    }
}

// Fetch Cart
$cart_items = [];
$total_price = 0;

// VULNERABLE: Direct concatenation in the cart fetch logic (if manipulating cookie/user_id were possible)
// But to make it easily exploitable, we will add an explicit SQLi parameter just for testing checkout flow
$cartQuery = "SELECT c.id as cart_id, c.quantity, p.id, p.name, p.price, p.image_url 
              FROM cart c JOIN products p ON c.product_id = p.id 
              WHERE c.user_id = " . $user_id;

$res = $conn->query($cartQuery);
if ($res) {
    while ($row = $res->fetch_assoc()) {
        $cart_items[] = $row;
        $total_price += ($row['price'] * $row['quantity']);
    }
}
$conn->close();

$tableRows = '';
if (empty($cart_items)) {
    $tableRows = '<tr><td colspan="5" style="text-align:center; padding:30px; color:#999;">Your cart is empty. <a href="/products.php" style="color:var(--primary);">Go shopping</a></td></tr>';
} else {
    foreach ($cart_items as $item) {
        $subtotal = number_format($item['price'] * $item['quantity'], 2);
        $img = htmlspecialchars($item['image_url'], ENT_QUOTES, 'UTF-8');
        $tableRows .= "
        <tr>
            <td style='padding:15px;'><img src='{$img}' style='width:50px; height:50px; border-radius:6px; object-fit:cover;' /></td>
            <td style='padding:15px; font-weight:bold;'>{$item['name']}</td>
            <td style='padding:15px;'>\${$item['price']}</td>
            <td style='padding:15px;'>{$item['quantity']}</td>
            <td style='padding:15px; font-weight:bold; color:var(--text-success);'>\${$subtotal}</td>
            <td style='padding:15px;'><a href='/cart.php?action=remove&cart_id={$item['cart_id']}' style='color:var(--error); text-decoration:none;'>❌ Remove</a></td>
        </tr>";
    }
}

$msgHtml = $message ? "<div class='alert alert-success' style='margin-bottom:20px;'>{$message}</div>" : '';
$totalFmt = number_format($total_price, 2);

$PAGE_CONTENT = <<<HTML
    <h1 class="page-title">🛒 Your Shopping Cart</h1>
    {$msgHtml}
    
    <div class="card" style="padding:0; overflow:hidden;">
        <table style="width:100%; border-collapse:collapse;">
            <thead style="background:rgba(255,255,255,0.05); border-bottom:1px solid var(--border-color); text-align:left;">
                <tr>
                    <th style="padding:15px;">Image</th>
                    <th style="padding:15px;">Product</th>
                    <th style="padding:15px;">Price</th>
                    <th style="padding:15px;">Quantity</th>
                    <th style="padding:15px;">Subtotal</th>
                    <th style="padding:15px;">Action</th>
                </tr>
            </thead>
            <tbody>{$tableRows}</tbody>
        </table>
    </div>

HTML;

if (!empty($cart_items)) {
    $PAGE_CONTENT .= <<<HTML
    <div class="card" style="margin-top:20px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <form method="POST" action="/cart.php?action=checkout" style="display:flex; gap:10px;">
                <input type="text" name="coupon" placeholder="Discount Code (Optional)">
                <button type="submit" class="btn" style="background:var(--success);">Secure Checkout</button>
            </form>
            <div style="font-size:12px; color:var(--text-secondary); margin-top:5px;">💡 Note: The coupon field is vulnerable to SQL Injection!</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:14px; color:var(--text-secondary);">Total Amount</div>
            <div style="font-size:32px; font-weight:bold; color:var(--text-success);">\${$totalFmt}</div>
        </div>
    </div>
HTML;
}

$PAGE_CONTENT .= '</div>';
include '/app/templates/app_template.php';
?>
PHP;
    } elseif ($page_name === 'orders') {
        return <<<'PHP'
<?php
session_start();
$user_id = $_SESSION['user_id'] ?? 1;

$order_id = $_GET['id'] ?? '';
$orders = [];
$conn = new mysqli('db', 'root', 'password', 'dvwa');

if (!$conn->connect_error) {
    if ($order_id !== '') {
        // VULNERABLE: Direct concatenation
        $query = "SELECT o.*, oi.quantity, oi.price as item_price, p.name 
                  FROM orders o 
                  JOIN order_items oi ON o.id = oi.order_id 
                  JOIN products p ON oi.product_id = p.id 
                  WHERE o.id = " . $order_id . " AND o.user_id = " . $user_id;
        
        // Use multi_query to support more dramatic exploiting on the orders page
        if ($conn->multi_query($query)) {
            do {
                if ($result = $conn->store_result()) {
                    while ($row = $result->fetch_assoc()) {
                        $orders[] = $row;
                    }
                    $result->free();
                }
            } while ($conn->more_results() && $conn->next_result());
        }
    } else {
        // Safe fetch of user's orders
        $query = "SELECT * FROM orders WHERE user_id = {$user_id} ORDER BY created_at DESC";
        $res = $conn->query($query);
        if ($res) {
            while ($row = $res->fetch_assoc()) {
                $orders[] = $row;
            }
        }
    }
    $conn->close();
}

$PAGE_CONTENT = <<<HTML
    <h1 class="page-title">📦 Order History</h1>
    <div class="card" style="margin-bottom:20px;">
        <form method="GET" style="display:flex; gap:10px;">
            <div class="form-group" style="flex:1; margin-bottom:0;">
                <label>Lookup Order ID (Invoices):</label>
                <input type="text" name="id" value="{$order_id}" placeholder="e.g. 1001" style="width:100%;">
            </div>
            <button class="btn" style="align-self:flex-end;">View Invoice</button>
        </form>
        <p style="margin-top:10px; font-size:13px; color:var(--text-secondary);">💡 This input is vulnerable to SQLi (e.g., <code>1 OR 1=1</code> to view all invoices)</p>
    </div>
HTML;

if ($order_id !== '') {
    // Show detailed invoice mode
    $PAGE_CONTENT .= '<div class="card"><div class="card-title">Invoice Results</div><table style="width:100%; text-align:left; border-collapse:collapse;">';
    $PAGE_CONTENT .= '<tr style="border-bottom:1px solid #333;"><th style="padding:10px;">Order ID</th><th style="padding:10px;">Product Name</th><th style="padding:10px;">Qty</th><th style="padding:10px;">Status</th></tr>';
    foreach ($orders as $o) {
        $name = htmlspecialchars($o['name'] ?? 'Unknown Item', ENT_QUOTES, 'UTF-8');
        $PAGE_CONTENT .= "<tr>
            <td style='padding:10px;'>#{$o['id']}</td>
            <td style='padding:10px;'>{$name}</td>
            <td style='padding:10px;'>{$o['quantity']}</td>
            <td style='padding:10px;'><span class='badge badge-info'>{$o['status']}</span></td>
        </tr>";
    }
    if (empty($orders)) {
        $PAGE_CONTENT .= "<tr><td colspan='4' style='padding:10px; text-align:center;'>No details found for this Order ID.</td></tr>";
    }
    $PAGE_CONTENT .= '</table></div>';
} else {
    // Show summary mode
    $PAGE_CONTENT .= '<div class="card"><div class="card-title">Your Recent Orders</div><table style="width:100%; text-align:left; border-collapse:collapse;">';
    $PAGE_CONTENT .= '<tr style="border-bottom:1px solid #333;"><th style="padding:10px;">Order ID</th><th style="padding:10px;">Date</th><th style="padding:10px;">Total</th><th style="padding:10px;">Status</th><th style="padding:10px;">Action</th></tr>';
    foreach ($orders as $o) {
        $dt = htmlspecialchars($o['created_at'], ENT_QUOTES, 'UTF-8');
        $PAGE_CONTENT .= "<tr>
            <td style='padding:10px; font-weight:bold;'>#{$o['id']}</td>
            <td style='padding:10px; color:#aaa;'>{$dt}</td>
            <td style='padding:10px; color:var(--text-success); font-weight:bold;'>\${$o['total_amount']}</td>
            <td style='padding:10px;'><span class='badge badge-success'>{$o['status']}</span></td>
            <td style='padding:10px;'><a href='?id={$o['id']}' style='color:var(--primary); font-size:14px; text-decoration:none;'>View Details</a></td>
        </tr>";
    }
    if (empty($orders)) {
        $PAGE_CONTENT .= "<tr><td colspan='5' style='padding:20px; text-align:center;'>You have not placed any orders yet.</td></tr>";
    }
    $PAGE_CONTENT .= '</table></div>';
}

$PAGE_CONTENT .= '</div>';
include '/app/templates/app_template.php';
?>
PHP;
    }
// Keep all other conditions the same!

    // GENERIC FALLBACK: Ensure any page assigned by generator actually exists    // GENERIC FALLBACK: Ensure any page assigned by generator actually exists
    return <<<'PHP'
<?php
session_start();
$input = $_REQUEST['id'] ?? $_REQUEST['q'] ?? $_REQUEST['input'] ?? '';

// VULNERABLE: Generic SQLi fallback
$query = "SELECT * FROM data WHERE input = '" . $input . "'";

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">📦 Data Portal</h1>
    <div class="card">
        <p>This page handles dynamic data requests.</p>
        <form method="GET">
            <label>Request ID/Query:</label>
            <input type="text" name="input" value="{$input}">
            <button class="btn">Execute</button>
        </form>
    </div>
HTML;
if ($input) {
    $PAGE_CONTENT .= '<div class="card"><p>Processing: <code>' . htmlspecialchars($query) . '</code></p></div>';
}
$PAGE_CONTENT .= '</div>';
include '/app/templates/app_template.php';
?>
PHP;
    return null;
}

function generateXSS($vuln) {
    $page_name = basename($vuln['location'], '.php');
    
    if ($page_name === 'search') {
        return generateSQLInjection($vuln); // Search has both SQLi and XSS
    } elseif ($page_name === 'products' || $page_name === 'orders' || $page_name === 'admin_users' || $page_name === 'login' || $page_name === 'admin_login' || $page_name === 'product_detail' || $page_name === 'cart' || $page_name === 'profile') {
        return generateSQLInjection($vuln); // Fallback to SQLi structure which also has XSS via reflected input
    } elseif ($page_name === 'support') {
        return <<<'PHP'
<?php
session_start();
$message = $_POST['message'] ?? '';
$tickets = $_SESSION['tickets'] ?? [];

if ($message) {
    // VULNERABLE: Stored XSS
    $tickets[] = ['msg' => $message];
    $_SESSION['tickets'] = $tickets;
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">🎧 Customer Support</h1>
    <div class="card">
        <form method="POST">
            <label>Describe your issue:</label>
            <textarea name="message" rows="4"></textarea>
            <button class="btn">Submit Ticket</button>
        </form>
    </div>
    <div class="card"><div class="card-title">Your Tickets</div>
HTML;
foreach ($tickets as $t) {
    $PAGE_CONTENT .= "<div style='padding:10px; border-bottom:1px solid #eee;'>{$t['msg']}</div>";
}
$PAGE_CONTENT .= '</div></div>';
include '/app/templates/app_template.php';
?>
PHP;

    } elseif ($page_name === 'index') {
        return <<<'PHP'
<?php
session_start();

$PAGE_CONTENT = <<<HTML
    <h1 class="page-title">🏠 SecureShop Home</h1>
    <div class="card">
        <h3>Welcome to SecureShop!</h3>
        <p>Your premier destination for all tech gadgets.</p>
        <div id="greeting"></div>
    </div>
    <!-- VULNERABLE: DOM XSS via hash -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var hash = decodeURIComponent(window.location.hash.substring(1));
            if (hash) {
                document.getElementById('greeting').innerHTML = "Welcome back: " + hash;
            }
        });
    </script>
</div>
HTML;
include '/app/templates/app_template.php';
?>
PHP;
    } elseif ($page_name === 'reviews') {
        return <<<'PHP'
<?php
session_start();
$_SESSION['username'] = 'admin';

$review = isset($_POST['review']) ? $_POST['review'] : '';
$reviews = isset($_SESSION['reviews']) ? $_SESSION['reviews'] : [];

if ($review) {
    // VULNERABLE: Stored XSS - no sanitization
    $reviews[] = ['author' => $_SESSION['username'], 'text' => $review, 'time' => date('Y-m-d H:i')];
    $_SESSION['reviews'] = $reviews;
}

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">⭐ Product Reviews</h1>
    
    <div class="card">
        <div class="card-title">Write a Review</div>
        <form method="POST">
            <div class="form-group">
                <label>Your Review</label>
                <textarea name="review" rows="4" placeholder="Share your experience..."></textarea>
            </div>
            <button type="submit" class="btn">Submit Review</button>
        </form>
    </div>
    
    <div class="card">
        <div class="card-title">Recent Reviews</div>
HTML;

foreach ($reviews as $r) {
    // VULNERABLE: Output without escaping
    $PAGE_CONTENT .= "<div style='padding:15px; background:white; border-radius:8px; margin-bottom:10px; border-left:4px solid #667eea;'>
        <strong>{$r['author']}</strong> <span style='color:#888; font-size:13px;'>• {$r['time']}</span>
        <p style='margin-top:8px;'>{$r['text']}</p>
    </div>";
}

$PAGE_CONTENT .= <<<HTML
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>
PHP;
    }
}

function generateMisconfig($vuln) {
    $page_name = basename($vuln['location'], '.php');
    
    if ($page_name === 'debug') {
        return <<<'PHP'
<?php
session_start();
$_SESSION['username'] = 'admin';

// VULNERABLE: Debug mode exposing sensitive info
$debug_info = [
    'PHP Version' => phpversion(),
    'Server Software' => $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown',
    'Document Root' => $_SERVER['DOCUMENT_ROOT'] ?? 'Unknown',
    'Database Host' => 'db',
    'Database User' => 'root',
    'API Keys' => 'sk_live_123456789abcdef',
    'Session ID' => session_id(),
];

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">🐛 Debug Console</h1>
    
    <div class="alert alert-error">
        ⚠️ Warning: Debug mode is enabled in production!
    </div>
    
    <div class="card">
        <div class="card-title">System Information</div>
        <table>
HTML;

foreach ($debug_info as $key => $value) {
    $PAGE_CONTENT .= "<tr><th>{$key}</th><td>{$value}</td></tr>";
}

$PAGE_CONTENT .= <<<HTML
        </table>
        <div style='margin-top:20px; padding:15px; background:#fff3cd; border-radius:8px; color:#856404;'>
            💡 <strong>Testing Tip:</strong> This page exposes sensitive configuration details
        </div>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>
PHP;
    }
}

function generateCSRF($vuln) {
    return <<<'PHP'
<?php
session_start();

// Temporary forced login for testing
if (!isset($_SESSION['user_id'])) {
    $_SESSION['username'] = 'admin';
}

$message = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // VULNERABLE: No CSRF protection
    if (!empty($_POST['new_password'])) {
        $message = "Password changed successfully! (Demo only - no real change)";
    }
}

// Pre-build message (safe heredoc)
$messageHtml = $message !== ''
    ? '<div class="alert alert-success" style="margin-bottom:20px; padding:15px; background:#efe; border:1px solid #cfc; border-radius:8px;">
           ✅ ' . htmlspecialchars($message, ENT_QUOTES, 'UTF-8') . '
       </div>'
    : '';

$testingTip = "💡 <strong>Testing Tip:</strong> This form has no CSRF protection. 
    Craft a malicious page on another domain that auto-submits this form when visited.";

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker" title="CSRF Vulnerability Present"></div>
    <h1 class="page-title">⚙️ Account Settings</h1>
    
    {$messageHtml}
    
    <div class="card">
        <div class="card-title">Change Password</div>
        <form method="POST">
            <div class="form-group">
                <label>Current Password</label>
                <input type="password" name="current_password" required>
            </div>
            <div class="form-group">
                <label>New Password</label>
                <input type="password" name="new_password" required>
            </div>
            <div class="form-group">
                <label>Confirm New Password</label>
                <input type="password" name="confirm_password" required>
            </div>
            <button type="submit" class="btn">Update Password</button>
        </form>
        
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>
PHP;
}

function generateSSRF($vuln) {
    return <<<'PHP'
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
PHP;
}

function generateXXE($vuln) {
    return <<<'PHP'
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
PHP;
}

function generateLFI($vuln) {
    return <<<'PHP'
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
PHP;
}

function generateRCE($vuln) {
    return <<<'PHP'
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
PHP;
}

function generateIDOR($vuln) {
    return <<<'PHP'
<?php
session_start();
$_SESSION['username'] = 'admin';

$orderId = isset($_GET['id']) ? $_GET['id'] : '1001';

// VULNERABLE: IDOR - no ownership check
$orders = [
    '1001' => ['customer' => 'John Doe', 'total' => '$149.99', 'items' => 'Laptop Case, Mouse'],
    '1002' => ['customer' => 'Jane Smith', 'total' => '$899.99', 'items' => 'Tablet Pro'],
    '1003' => ['customer' => 'Bob Johnson', 'total' => '$49.99', 'items' => 'USB Cable'],
];

$order = $orders[$orderId] ?? null;

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">📦 Order Details</h1>
    
    <div class="card">
        <form method="GET">
            <div class="form-group">
                <label>Order ID</label>
                <input type="text" name="id" value="{$orderId}" placeholder="Enter Order ID">
            </div>
            <button type="submit" class="btn">View Order</button>
        </form>
        <div style='margin-top:15px; padding:12px; background:#e7f3ff; border-radius:6px; color:#004085; font-size:14px;'>
            💡 <strong>Testing Tip:</strong> Try different order IDs: 1001, 1002, 1003
        </div>
    </div>
HTML;

if ($order) {
    $PAGE_CONTENT .= <<<HTML
    <div class="card">
        <div class="card-title">Order #{$orderId}</div>
        <table>
            <tr><th>Customer:</th><td>{$order['customer']}</td></tr>
            <tr><th>Total:</th><td><strong>{$order['total']}</strong></td></tr>
            <tr><th>Items:</th><td>{$order['items']}</td></tr>
            <tr><th>Status:</th><td><span class='badge badge-success'>Delivered</span></td></tr>
        </table>
    </div>
HTML;
} else {
    $PAGE_CONTENT .= '<div class="alert alert-error">Order not found</div>';
}

$PAGE_CONTENT .= '</div>';

include '/app/templates/app_template.php';
?>
PHP;
}

function generateOpenRedirect($vuln) {
    return <<<'PHP'
<?php
$redirect = isset($_GET['redirect']) ? $_GET['redirect'] : '';

if ($redirect) {
    // VULNERABLE: Open Redirect - no validation
    header("Location: " . $redirect);
    exit;
}

session_start();
$_SESSION['username'] = 'admin';

$PAGE_CONTENT = <<<HTML
<div style="position:relative;">
    <div class="vuln-marker"></div>
    <h1 class="page-title">👋 Logout</h1>
    
    <div class="card">
        <div class="card-title">You have been logged out</div>
        <p style='margin-bottom:20px; color:#666;'>Thank you for using SecureShop. Click below to return to login.</p>
        <a href="?redirect=/" class="btn" style='display:inline-block; text-decoration:none;'>Return to Home</a>
        <div style='margin-top:20px; padding:15px; background:#fff3cd; border-radius:8px; color:#856404;'>
            💡 <strong>Testing Tip:</strong> Try: <code>?redirect=https://evil.com</code>
        </div>
    </div>
</div>
HTML;

include '/app/templates/app_template.php';
?>
PHP;
}

// Main execution
try {
    logMessage("Starting vulnerability application...");
    
    if (!file_exists($configFile)) {
        throw new Exception("Configuration file not found: $configFile");
    }
    
    $config = json_decode(file_get_contents($configFile), true);
    
    if (!$config || !isset($config['vulnerabilities'])) {
        throw new Exception("Invalid configuration file");
    }
    
    $enabledVulns = array_filter($config['vulnerabilities'], function($v) {
        return $v['enabled'];
    });
    
    logMessage("Applying " . count($enabledVulns) . " vulnerabilities...");
    
    $createdFiles = createVulnerableFiles($config['vulnerabilities']);
    
    logMessage("Applied vulnerabilities successfully!");
    logMessage("Created " . count($createdFiles) . " vulnerable endpoints");
    
} catch (Exception $e) {
    logMessage("ERROR: " . $e->getMessage());
    exit(1);
}
?>