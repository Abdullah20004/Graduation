import random

categories = ['Laptops', 'Phones', 'Audio', 'Accessories', 'Monitors', 'Components', 'Gaming', 'Tablets', 'Cameras', 'Networking', 'Smart Home', 'Wearables']

brands = {
    'Laptops': ['Apple', 'Dell', 'Lenovo', 'HP', 'ASUS', 'Razer', 'Acer', 'Microsoft', 'Samsung'],
    'Phones': ['Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'Motorola', 'Nothing'],
    'Audio': ['Sony', 'Apple', 'Bose', 'Samsung', 'JBL', 'Sonos', 'Sennheiser', 'Audio-Technica'],
    'Accessories': ['Logitech', 'Corsair', 'Razer', 'Keychron', 'Anker', 'SteelSeries', 'HyperX'],
    'Monitors': ['Dell', 'LG', 'Samsung', 'ASUS', 'Acer', 'BenQ', 'Alienware'],
    'Components': ['NVIDIA', 'AMD', 'Intel', 'Samsung', 'Crucial', 'Corsair', 'ASUS', 'MSI'],
    'Gaming': ['Sony', 'Microsoft', 'Nintendo', 'Logitech', 'Razer'],
    'Tablets': ['Apple', 'Samsung', 'Lenovo', 'Microsoft', 'Amazon'],
    'Cameras': ['GoPro', 'DJI', 'Sony', 'Canon', 'Nikon', 'Insta360'],
    'Networking': ['ASUS', 'TP-Link', 'Netgear', 'Ubiquiti', 'Google', 'Linksys'],
    'Smart Home': ['Google', 'Amazon', 'Philips', 'Ring', 'Wyze', 'August'],
    'Wearables': ['Apple', 'Samsung', 'Garmin', 'Fitbit', 'Amazfit', 'Whoop']
}

descriptors = ['Pro', 'Ultra', 'Plus', 'Max', 'Lite', 'Mini', 'Slim', 'Elite', 'Essential', 'Advanced']

images = [
    'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400',
    'https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?w=400',
    'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=400',
    'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400',
    'https://images.unsplash.com/photo-1696446701796-da61225697cc?w=400',
    'https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400',
    'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400',
    'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400',
    'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400',
    'https://images.unsplash.com/photo-1622204364002-386617e90c8b?w=400',
    'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400',
    'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=400'
]

products = []

# Keep some original famous products
products.extend([
    "('Apple MacBook Pro 16\"', 'M3 Pro chip, 18GB RAM, 512GB SSD', 2499.99, 12, 'Laptops', 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400', 4.8)",
    "('Galaxy S24 Ultra', '6.8\" AMOLED, 200MP, Snapdragon 8 Gen 3', 1199.99, 28, 'Phones', 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400', 4.6)",
    "('Sony WH-1000XM5', 'Industry-leading noise cancelling', 349.99, 45, 'Audio', 'https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400', 4.7)",
    "('Logitech MX Master 3S', 'Wireless ergonomic mouse', 99.99, 120, 'Accessories', 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400', 4.5)",
    "('LG C3 55\" OLED', 'Self-lit pixels, 4K 120Hz', 1299.99, 8, 'Monitors', 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400', 4.8)",
    "('RTX 4090', '24GB GDDR6X, DLSS 3.0 GPU', 1599.99, 5, 'Components', 'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400', 4.9)",
])

# Generate random products until we have 120
for i in range(len(products), 120):
    cat = random.choice(categories)
    brand = random.choice(brands[cat])
    desc = random.choice(descriptors)
    
    version = random.randint(2, 9)
    if random.choice([True, False]):
        name = f"{brand} {cat[:-1]} {version} {desc}"
    else:
        name = f"{brand} X{version}00 {desc}"
        
    description = f"Latest generation {cat[:-1]} with advanced features. Perfect for everyday use."
    price = round(random.uniform(49.99, 1999.99), 2)
    stock = random.randint(0, 150)
    img = random.choice(images)
    rating = round(random.uniform(3.5, 5.0), 1)
    
    val = f"('{name}', '{description}', {price}, {stock}, '{cat}', '{img}', {rating})"
    products.append(val)

sql = "INSERT INTO products (name, description, price, stock, category, image_url, rating) VALUES\n"
sql += ",\n".join(products) + ";\n"

print(sql)

with open('d:/graduation_project/HackOps/generated_products.sql', 'w') as f:
    f.write(sql)
