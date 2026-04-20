SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS access_log;
DROP TABLE IF EXISTS security_log;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    category VARCHAR(50),
    image_url VARCHAR(500) DEFAULT '',
    rating DECIMAL(2,1) DEFAULT 4.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    rating INT DEFAULT 5,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Seed default users (password is 'password')
INSERT IGNORE INTO users (username, email, password, role) VALUES
('admin', 'admin@secureshop.com', '$2y$10$8K1p/a0dL3LKzOqS8/rQHuV6WJ6p2dQoP.vYV7fGP4L9CjPqP0/vG', 'admin'),
('john_doe', 'john@example.com', '$2y$10$8K1p/a0dL3LKzOqS8/rQHuV6WJ6p2dQoP.vYV7fGP4L9CjPqP0/vG', 'user'),
('jane_smith', 'jane@example.com', '$2y$10$8K1p/a0dL3LKzOqS8/rQHuV6WJ6p2dQoP.vYV7fGP4L9CjPqP0/vG', 'user');

-- Seed some products
INSERT INTO products (name, description, price, stock, category, image_url, rating) VALUES
('Apple MacBook Pro 16"', 'M3 Pro chip, 18GB RAM, 512GB SSD', 2499.99, 12, 'Laptops', 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400', 4.8),
('Dell XPS 15', '13th Gen Intel i7, 16GB RAM, OLED display', 1799.99, 18, 'Laptops', 'https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=400', 4.6),
('ThinkPad X1 Carbon', 'Intel i7, 32GB RAM, legendary keyboard', 1649.99, 14, 'Laptops', 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400', 4.5),
('GoPro HERO 12', '5.3K video action camera', 399.99, 15, 'Cameras', 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=400', 4.6),
('DJI Mini 4 Pro', 'Under 249g drone, 4K video', 759.99, 10, 'Cameras', 'https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400', 4.9);

SET FOREIGN_KEY_CHECKS = 1;
