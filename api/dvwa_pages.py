"""
DVWA E-Commerce Page Definitions
Defines all available pages with their features for realistic vulnerability assignment
"""

DVWA_PAGES = {
    # ========== PUBLIC PAGES ==========
    "index.php": {
        "name": "Home",
        "category": "public",
        "features": ["display_products", "client_side_processing", "user_input"],
        "description": "E-commerce homepage with featured products"
    },
    "products.php": {
        "name": "Products",
        "category": "catalog",
        "features": ["user_input", "database_query", "display_results", "search_metadata"],
        "description": "Product catalog listing with pagination"
    },
    "search.php": {
        "name": "Search",
        "category": "catalog",
        "features": ["user_input", "database_query", "display_results", "search_metadata"],
        "description": "Product search with filters"
    },
    "product_detail.php": {
        "name": "Product Details",
        "category": "catalog",
        "features": ["user_input", "database_query", "display_product_data", "display_results", "id_parameter"],
        "description": "Individual product page with details and reviews"
    },
    "support.php": {
        "name": "Support",
        "category": "public",
        "features": ["user_input", "database_write", "display_results", "form_echo"],
        "description": "Contact customer support form"
    },
    
    # ========== AUTHENTICATION ==========
    "login.php": {
        "name": "Login",
        "category": "auth",
        "features": ["user_input", "database_query", "authentication", "form_echo"],
        "description": "Customer login page"
    },
    "register.php": {
        "name": "Register",
        "category": "auth",
        "features": ["user_input", "database_write", "database_query", "form_echo"],
        "description": "New customer registration form"
    },
    
    # ========== SHOPPING ==========
    "cart.php": {
        "name": "Shopping Cart",
        "category": "shopping",
        "features": ["user_input", "session_data", "display_user_data"],
        "description": "View and manage shopping cart"
    },
    "checkout.php": {
        "name": "Checkout",
        "category": "shopping",
        "features": ["user_input", "database_write", "payment_processing"],
        "description": "Complete purchase and payment"
    },
    
    # ========== USER ACCOUNT ==========
    "profile.php": {
        "name": "My Profile",
        "category": "account",
        "features": ["user_input", "database_query", "display_user_data"],
        "description": "User account profile management"
    },
    "orders.php": {
        "name": "Order History",
        "category": "account",
        "features": ["user_input", "database_query", "display_user_data"],
        "description": "View past orders and tracking"
    },
    "reviews.php": {
        "name": "My Reviews",
        "category": "account",
        "features": ["user_input", "database_write", "display_results"],
        "description": "Write and manage product reviews"
    },
    
    # ========== ADMIN PANEL ==========
    "admin_login.php": {
        "name": "Admin Login",
        "category": "admin",
        "features": ["user_input", "database_query", "authentication", "privileged"],
        "description": "Administrator authentication"
    },
    "admin_dashboard.php": {
        "name": "Admin Dashboard",
        "category": "admin",
        "features": ["user_input", "database_query", "display_admin_data", "privileged"],
        "description": "Admin control panel and statistics"
    },
    "admin_users.php": {
        "name": "User Management",
        "category": "admin",
        "features": ["user_input", "database_query", "display_user_data", "privileged"],
        "description": "Manage customer accounts and permissions"
    }
}

# Feature requirements for each vulnerability type
VULNERABILITY_REQUIREMENTS = {
    "sqli": {
        "required_any": [
            ["user_input", "database_query"],  # Most SQLi
            ["user_input", "database_write"],   # Insert/Update SQLi
        ]
    },
    "xss": {
        "required_any": [
            ["user_input", "display_results"],      # Reflected XSS
            ["user_input", "display_user_data"],    # Reflected in profile
            ["user_input", "display_product_data"], # Reflected in products
            ["client_side_processing", "user_input"] # DOM-based XSS
        ]
    }
}

def get_compatible_pages(vuln_type, all_pages=None):
    """
    Returns list of pages compatible with a given vulnerability type
    
    Args:
        vuln_type: Type of vulnerability (sqli, xss)
        all_pages: Optional dict of pages (defaults to DVWA_PAGES)
    
    Returns:
        List of page paths that can host this vulnerability type
    """
    if all_pages is None:
        all_pages = DVWA_PAGES
    
    requirements = VULNERABILITY_REQUIREMENTS.get(vuln_type, {})
    required_any = requirements.get("required_any", [])
    
    compatible = []
    
    for page_path, page_info in all_pages.items():
        page_features = set(page_info.get("features", []))
        
        # Check if page has any of the required feature combinations
        for feature_set in required_any:
            if all(feature in page_features for feature in feature_set):
                compatible.append(page_path)
                break  # Found a match, no need to check other combinations
    
    return compatible


def get_all_pages():
    """Returns all page definitions"""
    return DVWA_PAGES


def get_page_info(page_path):
    """Get information about a specific page"""
    return DVWA_PAGES.get(page_path)
