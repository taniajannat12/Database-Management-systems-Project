-- Categories Table
CREATE TABLE IF NOT EXISTS shop_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Table
CREATE TABLE IF NOT EXISTS shop_product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    category_id INT,
    stock INT DEFAULT 0,
    available BOOLEAN DEFAULT TRUE,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES shop_category(id)
);

-- Cart Table
CREATE TABLE IF NOT EXISTS shop_cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

-- Cart Items Table
CREATE TABLE IF NOT EXISTS shop_cartitem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cart_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES shop_cart(id),
    FOREIGN KEY (product_id) REFERENCES shop_product(id)
);

-- Orders Table
CREATE TABLE IF NOT EXISTS shop_order (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    delivery_address TEXT,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

-- Order Items Table
CREATE TABLE IF NOT EXISTS shop_orderitem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES shop_order(id),
    FOREIGN KEY (product_id) REFERENCES shop_product(id)
);
-- Categories insert
INSERT INTO shop_category (name) VALUES 
('Skin Care'),
('Makeup'),
('Hair Care');

-- Skin Care Products (15)
INSERT INTO shop_product (name, price, description, category_id, stock) VALUES
('Vitamin C Serum', 29.99, 'Brightening serum for glowing skin', 1, 50),
('Hyaluronic Acid Moisturizer', 24.99, 'Deep hydration for all skin types', 1, 30),
('Sunscreen SPF 50', 18.99, 'UV protection lotion', 1, 75),
('Retinol Night Cream', 34.99, 'Anti-aging night treatment', 1, 25),
('Face Wash', 12.99, 'Gentle cleanser for daily use', 1, 100),
('AHA BHA Exfoliator', 22.99, 'Chemical exfoliation solution', 1, 40),
('Niacinamide Serum', 19.99, 'Pore refining and oil control', 1, 60),
('Eye Cream', 27.99, 'Dark circle reduction cream', 1, 35),
('Clay Face Mask', 16.99, 'Deep cleansing mask', 1, 45),
('Facial Toner', 14.99, 'pH balancing toner', 1, 70),
('Acne Spot Treatment', 15.99, 'Targeted acne solution', 1, 55),
('Brightening Essence', 31.99, 'Skin brightening treatment', 1, 20),
('Lip Sleeping Mask', 13.99, 'Overnight lip treatment', 1, 80),
('Face Oil', 28.99, 'Nourishing facial oil', 1, 30),
('BB Cream', 21.99, 'Tinted moisturizer with SPF', 1, 65);

-- Makeup Products (15)
INSERT INTO shop_product (name, price, description, category_id, stock) VALUES
('Matte Lipstick', 22.99, 'Long-lasting matte finish lipstick', 2, 50),
('Foundation', 29.99, 'Natural finish liquid foundation', 2, 40),
('Mascara', 18.99, 'Volumizing and lengthening mascara', 2, 60),
('Eyeshadow Palette', 45.99, '12-color professional eyeshadow palette', 2, 25),
('Blush', 19.99, 'Natural blush for cheek color', 2, 45),
('Concealer', 24.99, 'Full coverage concealer', 2, 55),
('Makeup Setting Spray', 16.99, 'Long-lasting makeup setting', 2, 65),
('Eyebrow Pencil', 14.99, 'Precise eyebrow defining pencil', 2, 70),
('Lip Gloss', 15.99, 'Shiny non-sticky lip gloss', 2, 50),
('Highlighter', 21.99, 'Luminous face highlighter', 2, 35),
('Makeup Brushes Set', 39.99, '8-piece professional brush set', 2, 30),
('BB Cream', 26.99, 'Tinted moisturizer with SPF', 2, 45),
('Eyeliner', 17.99, 'Waterproof liquid eyeliner', 2, 55),
('Makeup Remover', 12.99, 'Gentle makeup removing solution', 2, 75),
('Pressed Powder', 20.99, 'Oil-control pressed powder', 2, 40);

-- Hair Care Products (15)
INSERT INTO shop_product (name, price, description, category_id, stock) VALUES
('Argan Oil Shampoo', 18.99, 'Nourishing shampoo with Argan oil', 3, 60),
('Keratin Conditioner', 22.99, 'Smoothing keratin conditioner', 3, 45),
('Hair Growth Serum', 29.99, 'Stimulates hair growth', 3, 30),
('Anti-Dandruff Shampoo', 16.99, 'Fights dandruff effectively', 3, 70),
('Hair Mask Treatment', 24.99, 'Deep conditioning hair mask', 3, 35),
('Hair Oil', 19.99, 'Nourishing hair oil blend', 3, 50),
('Scalp Scrub', 14.99, 'Exfoliating scalp treatment', 3, 40),
('Leave-in Conditioner', 17.99, 'Daily leave-in conditioner', 3, 55),
('Hair Spray', 12.99, 'Strong hold hair spray', 3, 65),
('Hair Serum', 21.99, 'Frizz control serum', 3, 40),
('Color Protection Shampoo', 20.99, 'For color-treated hair', 3, 35),
('Volume Booster', 23.99, 'Adds volume to fine hair', 3, 30),
('Split Ends Treatment', 18.99, 'Repairs split ends', 3, 45),
('Dry Shampoo', 15.99, 'Quick refresh between washes', 3, 60),
('Hair Vitamins', 34.99, 'Nutritional supplements for hair', 3, 25);