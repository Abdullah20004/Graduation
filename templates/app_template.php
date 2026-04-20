<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecureShop | Premium Training Platform</title>
    <!-- Premium Typography -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #05060f;
            --bg-secondary: #0a0c1a;
            --accent: #7c4dff;
            --accent-gradient: linear-gradient(135deg, #7c4dff 0%, #448aff 100%);
            --accent-glow: rgba(124, 77, 255, 0.4);
            --glass: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-hover: rgba(255, 255, 255, 0.06);
            --text-primary: #ffffff;
            --text-secondary: #a0a0c0;
            --text-muted: #62627a;
            --success: #00e676;
            --danger: #ff5252;
            --warning: #ffab40;
            --radius-lg: 24px;
            --radius-md: 16px;
            --radius-sm: 12px;
            --transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        }

        body.light-theme {
            --bg-primary: #f5f7ff;
            --bg-secondary: #ffffff;
            --accent: #6200ea;
            --glass: rgba(0, 0, 0, 0.02);
            --glass-border: rgba(0, 0, 0, 0.08);
            --glass-hover: rgba(0, 0, 0, 0.04);
            --text-primary: #1a1a2e;
            --text-secondary: #5a5a7a;
            --text-muted: #8a8aa0;
            --border: rgba(0, 0, 0, 0.05);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: var(--bg-primary); }
        ::-webkit-scrollbar-thumb { background: var(--glass-border); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
        }

        /* Ambient Background */
        .ambient-bg {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: -1;
            overflow: hidden;
            background: var(--bg-primary);
        }
        .blob {
            position: absolute;
            background: var(--accent-gradient);
            filter: blur(120px);
            border-radius: 50%;
            opacity: 0.15;
            animation: move 25s infinite alternate;
        }
        @keyframes move {
            0% { transform: translate(-10%, -10%) scale(1); }
            100% { transform: translate(10%, 10%) scale(1.2); }
        }

        .container { max-width: 1300px; margin: 0 auto; padding: 20px 40px; width: 100%; }

        /* Navigation */
        .glass-nav {
            margin-top: 20px;
            background: var(--glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-lg);
            padding: 12px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            animation: slideDown 0.8s ease;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 24px;
            letter-spacing: -0.5px;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .nav-links { display: flex; gap: 10px; }
        .nav-links a {
            padding: 10px 18px;
            border-radius: var(--radius-sm);
            text-decoration: none;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 600;
            transition: var(--transition);
        }
        .nav-links a:hover, .nav-links a.active {
            color: var(--text-primary);
            background: var(--glass-hover);
            transform: translateY(-1px);
        }

        /* Standard Components */
        .main-content {
            margin-top: 40px;
            flex-grow: 1;
            animation: fadeIn 1s ease;
        }

        .card {
            background: var(--glass);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-md);
            padding: 30px;
            margin-bottom: 24px;
            transition: var(--transition);
        }
        .card:hover { 
            border-color: rgba(255,255,255,0.15); 
            background: var(--glass-hover);
            transform: translateY(-4px); 
        }

        .page-title {
            font-family: 'Outfit', sans-serif;
            font-size: 38px;
            font-weight: 800;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .form-group { margin-bottom: 24px; }
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
        }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 16px 20px;
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-family: inherit;
            font-size: 15px;
            transition: var(--transition);
        }
        .form-group input:focus {
            outline: none;
            border-color: var(--accent);
            background: rgba(0,0,0,0.3);
            box-shadow: 0 0 20px var(--accent-glow);
        }

        .btn {
            background: var(--accent-gradient);
            color: white;
            padding: 14px 32px;
            border-radius: var(--radius-sm);
            border: none;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: 0 8px 20px var(--accent-glow);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 30px var(--accent-glow);
            filter: brightness(1.15);
        }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 30px;
        }
        .product-card {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-md);
            overflow: hidden;
            transition: var(--transition);
        }
        .product-card:hover {
            transform: translateY(-8px);
            border-color: var(--accent);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .image-wrapper { height: 200px; overflow: hidden; background: #000; }
        .product-image { width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s ease; }
        .product-card:hover .product-image { transform: scale(1.1); }
        .product-body { padding: 25px; }

        .badge {
            padding: 4px 12px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
        }
        .badge-success { background: rgba(0, 230, 118, 0.15); color: var(--success); }

        /* Animations */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-30px); } to { opacity: 1; transform: translateY(0); } }

        .footer {
            margin-top: 80px;
            padding: 40px;
            text-align: center;
            color: var(--text-muted);
            font-size: 14px;
            border-top: 1px solid var(--glass-border);
        }

        /* ── Auth Pages ───────────────────────────────────── */
        .auth-wrap {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 70vh;
            padding: 40px 20px;
        }
        .auth-card {
            width: 100%;
            max-width: 440px;
            background: var(--glass);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-lg);
            padding: 48px 40px;
            box-shadow: 0 30px 80px rgba(0,0,0,0.4);
            animation: fadeIn 0.6s ease;
        }
        .auth-icon {
            font-size: 52px;
            text-align: center;
            margin-bottom: 20px;
            filter: drop-shadow(0 0 20px var(--accent-glow));
        }
        .auth-title {
            font-family: 'Outfit', sans-serif;
            font-size: 30px;
            font-weight: 800;
            text-align: center;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        .auth-sub {
            text-align: center;
            color: var(--text-muted);
            font-size: 14px;
            margin-bottom: 30px;
        }
        .auth-form .form-group { margin-bottom: 18px; }
        .auth-btn { width: 100%; padding: 16px; font-size: 15px; margin-top: 8px; justify-content: center; }
        .auth-link {
            text-align: center;
            margin-top: 24px;
            font-size: 13px;
            color: var(--text-muted);
        }
        .auth-link a {
            color: var(--accent);
            text-decoration: none;
            font-weight: 700;
        }
        .auth-link a:hover { text-decoration: underline; }

        /* ── Alerts ───────────────────────────────────────── */
        .alert-error {
            background: rgba(255,82,82,0.1);
            border: 1px solid rgba(255,82,82,0.25);
            color: #ff5252;
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 18px;
        }
        .alert-success {
            background: rgba(0,230,118,0.1);
            border: 1px solid rgba(0,230,118,0.25);
            color: var(--success);
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 18px;
        }

        /* ── Product Cards ────────────────────────────────── */
        .product-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
            margin-bottom: 16px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .product-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 16px;
        }
        .stars { color: #f1c40f; font-size: 14px; letter-spacing: 2px; }
        .rating-num { font-size: 12px; color: var(--text-muted); font-weight: 600; }
        .product-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: auto;
        }
        .product-price {
            font-size: 20px;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* ── Page Headers ─────────────────────────────────── */
        .page-header {
            margin-bottom: 40px;
        }
        .page-header h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .page-header p {
            color: var(--text-secondary);
            margin-top: 6px;
            font-size: 15px;
        }

        /* ── Table ────────────────────────────────────────── */
        table { width: 100%; border-collapse: collapse; }
        th {
            text-align: left;
            padding: 12px 16px;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--glass-border);
        }
        td {
            padding: 14px 16px;
            font-size: 14px;
            color: var(--text-secondary);
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        tr:hover td { background: var(--glass-hover); color: var(--text-primary); }

        /* ── Misc ─────────────────────────────────────────── */
        .card-title {
            font-size: 13px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            margin-bottom: 20px;
        }
        textarea {
            width: 100%;
            padding: 14px 18px;
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-family: inherit;
            font-size: 14px;
            transition: var(--transition);
        }
        textarea:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 20px var(--accent-glow);
        }
        select {
            width: 100%;
            padding: 14px 18px;
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-family: inherit;
            font-size: 14px;
            transition: var(--transition);
            -webkit-appearance: none;
        }
        select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 20px var(--accent-glow);
        }
        input[type=number] {
            width: 70px;
            padding: 8px 10px;
            background: rgba(0,0,0,0.2);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 14px;
            text-align: center;
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const theme = localStorage.getItem('theme') || 'dark';
            if (theme === 'light') document.body.classList.add('light-theme');
        });
        function toggleTheme() {
            document.body.classList.toggle('light-theme');
            localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
        }
    </script>
</head>
<body>
    <div class="ambient-bg">
        <div class="blob" style="width: 400px; height: 400px; top: -100px; right: -100px;"></div>
        <div class="blob" style="width: 500px; height: 500px; bottom: -200px; left: -200px; animation-delay: -5s;"></div>
    </div>

    <div class="container" style="display:flex; flex-direction:column; min-height:100vh;">
        <nav class="glass-nav">
            <a href="/index.php" class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 8px var(--accent-glow))">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
                SecureShop
            </a>
            
            <div class="nav-links">
                <a href="/index.php" class="<?php echo basename($_SERVER['PHP_SELF']) == 'index.php' ? 'active' : ''; ?>">Home</a>
                <a href="/products.php" class="<?php echo in_array(basename($_SERVER['PHP_SELF']), ['products.php', 'product.php']) ? 'active' : ''; ?>">Store</a>
                <?php if (isset($_SESSION['user_id'])): ?>
                    <a href="/search.php" class="<?php echo basename($_SERVER['PHP_SELF']) == 'search.php' ? 'active' : ''; ?>">Search</a>
                    <a href="/orders.php" class="<?php echo basename($_SERVER['PHP_SELF']) == 'orders.php' ? 'active' : ''; ?>">Orders</a>
                    <a href="/reviews.php" class="<?php echo basename($_SERVER['PHP_SELF']) == 'reviews.php' ? 'active' : ''; ?>">Reviews</a>
                    <a href="/support.php" class="<?php echo basename($_SERVER['PHP_SELF']) == 'support.php' ? 'active' : ''; ?>">Support</a>
                <?php endif; ?>
            </div>
            <div style="display:flex; align-items:center; gap:20px;">
                <button onclick="toggleTheme()" style="background:none; border:none; cursor:pointer; font-size:18px;">🌙</button>
                <?php if (isset($_SESSION['user_id'])): ?>
                    <a href="/cart.php" style="text-decoration:none; font-size: 20px;">🛒</a>
                    <div style="display:flex; align-items:center; gap:12px; background:rgba(255,255,255,0.05); padding:6px 16px; border-radius:50px;">
                        <span style="font-size:13px; font-weight:700; color:var(--text-secondary);">
                            <?php echo htmlspecialchars($_SESSION['username'] ?? 'User'); ?>
                        </span>
                        <a href="/logout.php" style="color:var(--danger); text-decoration:none; font-size:12px; font-weight:700;">Logout</a>
                    </div>
                <?php else: ?>
                    <a href="/login.php" class="btn" style="padding:10px 24px;">Login</a>
                <?php endif; ?>
            </div>
        </nav>

        <main class="main-content">
            <?php echo $PAGE_CONTENT ?? ''; ?>
        </main>

        <footer class="footer">
            <p>&copy; 2026 <strong>SecureShop</strong> &middot; Professional Training Environment</p>
        </footer>
    </div>
</body>
</html>