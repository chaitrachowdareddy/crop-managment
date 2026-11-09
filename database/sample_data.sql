-- =============================================================================
-- Crop Supply Chain Management System
-- Sample Dataset (MySQL)
-- Realistic Indian Agricultural Supply Chain Data
-- =============================================================================

USE crop_management;

-- Safe bulk population: executes idempotently without deleting existing data.
SET FOREIGN_KEY_CHECKS = 0;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 1. Insert Farmers (12 Farmers from different agricultural regions)
-- =============================================================================
INSERT IGNORE INTO Farmer (farmer_id, name, phone, address, village, registration_date) VALUES
(1, 'Gurpreet Singh', '9876543210', 'House 42, GT Road', 'Samana, Patiala', '2023-01-15'),
(2, 'Ramesh Patel', '9876543211', 'Plot 18, Station Road', 'Bardoli, Surat', '2023-02-10'),
(3, 'Suresh Gowda', '9876543212', 'Near Temple, Main St', 'Pandavapura, Mandya', '2023-03-05'),
(4, 'Manoj Deshmukh', '9876543213', 'Farm House 7', 'Niphad, Nashik', '2023-03-20'),
(5, 'Venkat Rao', '9876543214', 'D.No 4-55, Canal Road', 'Tenali, Guntur', '2023-04-12'),
(6, 'Balram Yadav', '9876543215', 'Village Post office', 'Chandausi, Sambhal', '2023-05-18'),
(7, 'Rajesh Sharma', '9876543216', 'Bypass Road, Ward 3', 'Karnal, Haryana', '2023-06-01'),
(8, 'Anand Kumar', '9876543217', 'Kaveri Basin Farm', 'Tiruchirappalli, Tamil Nadu', '2023-07-22'),
(9, 'Harpreet Kaur', '9876543218', 'Near Canal bridge', 'Moga, Punjab', '2023-08-14'),
(10, 'Shivanna Gowda', '9876543219', 'Cross Road 2', 'Channapatna, Ramanagara', '2023-09-09'),
(11, 'Dinesh Choudhary', '9876543220', 'Kisan Nagar, Gali 4', 'Nagaur, Rajasthan', '2023-10-11'),
(12, 'Lakshmi Devi', '9876543221', 'East Street Farm', 'Chittoor, Andhra Pradesh', '2023-11-05');

-- =============================================================================
-- 2. Insert Crops (10 Diverse Agricultural Crops)
-- =============================================================================
INSERT IGNORE INTO Crop (crop_id, crop_name, crop_type, unit) VALUES
(1, 'Rice (Basmati)', 'Cereal', 'Quintal'),
(2, 'Wheat (Sharbati)', 'Cereal', 'Quintal'),
(3, 'Ragi (Finger Millet)', 'Millet / Grain', 'Quintal'),
(4, 'Maize (Yellow Corn)', 'Cereal / Fodder', 'Quintal'),
(5, 'Sugarcane', 'Cash Crop', 'Ton'),
(6, 'Cotton (Bt Long Staple)', 'Fiber / Cash Crop', 'Quintal'),
(7, 'Tomato (Hybrid Red)', 'Vegetable', 'Quintal'),
(8, 'Potato (Kufri Jyoti)', 'Vegetable / Tuber', 'Quintal'),
(9, 'Onion (Nashik Red)', 'Vegetable', 'Quintal'),
(10, 'Soybean (Yellow)', 'Oilseed / Pulse', 'Quintal');

-- =============================================================================
-- 3. Insert Crop Production Logs
-- =============================================================================
INSERT IGNORE INTO Production (production_id, farmer_id, crop_id, quantity, production_date, season) VALUES
(1, 1, 1, 250.00, '2023-11-10', 'Kharif'),
(2, 1, 2, 320.00, '2024-04-05', 'Rabi'),
(3, 2, 5, 450.00, '2023-12-15', 'Year-round'),
(4, 3, 3, 180.00, '2023-10-25', 'Kharif'),
(5, 4, 9, 350.00, '2023-11-30', 'Kharif'),
(6, 4, 7, 120.00, '2024-01-15', 'Rabi'),
(7, 5, 1, 280.00, '2023-11-20', 'Kharif'),
(8, 6, 8, 400.00, '2024-02-10', 'Rabi'),
(9, 7, 2, 310.00, '2024-04-12', 'Rabi'),
(10, 8, 1, 220.00, '2023-12-05', 'Kharif'),
(11, 9, 10, 190.00, '2023-10-18', 'Kharif'),
(12, 10, 3, 140.00, '2023-11-08', 'Kharif'),
(13, 11, 6, 160.00, '2023-12-20', 'Kharif'),
(14, 12, 7, 210.00, '2024-02-18', 'Zaid');

-- =============================================================================
-- 4. Insert Collection Centers (5 Strategic Agricultural Mandis / Hubs)
-- =============================================================================
INSERT IGNORE INTO Collection_Center (center_id, center_name, location, manager_name, contact) VALUES
(1, 'Patiala APMC Grain Center', 'Grain Market Yard, Patiala, Punjab', 'Jasbir Singh', '9811122233'),
(2, 'Mandya Kisan Agro Center', 'Sugar Town Road, Mandya, Karnataka', 'Pradeep Gowda', '9822233344'),
(3, 'Nashik Onion & Veg Mandi', 'Market Yard, Pimpalgaon, Nashik, MH', 'Sunil Jadhav', '9833344455'),
(4, 'Guntur Mirchi & Paddy Hub', 'Agricultural Market Yard, Guntur, AP', 'K. V. Subbarao', '9844455566'),
(5, 'Karnal Wheat Procure Center', 'NH-44 Bypass, Karnal, Haryana', 'Rakesh Verma', '9855566677');

-- =============================================================================
-- 5. Insert Crop Supply Records (Farmer -> Collection Center)
-- =============================================================================
INSERT IGNORE INTO Crop_Supply (supply_id, farmer_id, crop_id, center_id, quantity, price_per_unit, total_amount, supply_date) VALUES
(1, 1, 1, 1, 200.00, 3800.00, 760000.00, '2023-11-15'),
(2, 1, 2, 1, 300.00, 2275.00, 682500.00, '2024-04-10'),
(3, 3, 3, 2, 150.00, 3200.00, 480000.00, '2023-11-02'),
(4, 4, 9, 3, 300.00, 1800.00, 540000.00, '2023-12-05'),
(5, 4, 7, 3, 100.00, 1400.00, 140000.00, '2024-01-20'),
(6, 5, 1, 4, 250.00, 3650.00, 912500.00, '2023-11-25'),
(7, 6, 8, 5, 350.00, 1250.00, 437500.00, '2024-02-15'),
(8, 7, 2, 5, 280.00, 2300.00, 644000.00, '2024-04-15'),
(9, 8, 1, 2, 190.00, 3700.00, 703000.00, '2023-12-10'),
(10, 9, 10, 1, 170.00, 4600.00, 782000.00, '2023-10-25'),
(11, 10, 3, 2, 120.00, 3150.00, 378000.00, '2023-11-12'),
(12, 12, 7, 4, 180.00, 1350.00, 243000.00, '2024-02-22');

-- =============================================================================
-- 6. Insert Warehouses (4 Central State Storage Hubs)
-- =============================================================================
INSERT IGNORE INTO Warehouse (warehouse_id, warehouse_name, location, capacity) VALUES
(1, 'Central Silo & Warehouse - Ambala', 'GT Road, Ambala Industrial Area, Haryana', 5000.00),
(2, 'Deccan Agro Cold Storage - Pune', 'Chakan MIDC Phase 2, Pune, Maharashtra', 3500.00),
(3, 'South India Grain Silo - Bangalore Rural', 'Dabaspet Industrial Area, Nelamangala, KA', 4000.00),
(4, 'Coastal Andhra Logistics Hub - Guntur', 'Autonagar, Guntur Port Road, AP', 3000.00);

-- =============================================================================
-- 7. Insert Warehouse Inventory (Live Stock Levels)
-- =============================================================================
INSERT IGNORE INTO Inventory (inventory_id, warehouse_id, crop_id, quantity) VALUES
(1, 1, 1, 950.00),   -- Rice in Ambala
(2, 1, 2, 1400.00),  -- Wheat in Ambala
(3, 1, 10, 420.00),  -- Soybean in Ambala
(4, 2, 7, 280.00),   -- Tomato in Pune Cold Storage
(5, 2, 8, 650.00),   -- Potato in Pune Cold Storage
(6, 2, 9, 820.00),   -- Onion in Pune Cold Storage
(7, 3, 1, 600.00),   -- Rice in Bangalore
(8, 3, 3, 450.00),   -- Ragi in Bangalore
(9, 3, 4, 380.00),   -- Maize in Bangalore
(10, 4, 1, 720.00),  -- Rice in Guntur
(11, 4, 6, 260.00),  -- Cotton in Guntur
(12, 4, 7, 190.00);  -- Tomato in Guntur

-- =============================================================================
-- 8. Insert Wholesale Distributors (4 Distributors)
-- =============================================================================
INSERT IGNORE INTO Distributor (distributor_id, distributor_name, phone, address) VALUES
(1, 'Kisan Agro Traders & Wholesalers', '9711001122', 'Commercial Complex, Sector 18, Chandigarh'),
(2, 'Bharat Grain Wholesalers Pvt Ltd', '9722002233', 'Market Yard Gate 4, Gultekdi, Pune'),
(3, 'Deccan Agri Commodities Corp', '9733003344', 'APMC Yard, Yeshwanthpur, Bangalore'),
(4, 'Sri Venkateswara Agro Distributors', '9744004455', 'Brodipet 3rd Line, Guntur, AP');

-- =============================================================================
-- 9. Insert Distributor Purchases (From Warehouses)
-- =============================================================================
INSERT IGNORE INTO Purchase (purchase_id, distributor_id, warehouse_id, crop_id, quantity, price_per_unit, total_price, purchase_date) VALUES
(1, 1, 1, 1, 120.00, 4200.00, 504000.00, '2024-01-10'),
(2, 1, 1, 2, 200.00, 2550.00, 510000.00, '2024-04-20'),
(3, 2, 2, 9, 180.00, 2100.00, 378000.00, '2024-01-25'),
(4, 2, 2, 8, 150.00, 1500.00, 225000.00, '2024-02-28'),
(5, 3, 3, 3, 100.00, 3600.00, 360000.00, '2024-02-05'),
(6, 3, 3, 1, 140.00, 4150.00, 581000.00, '2024-03-12'),
(7, 4, 4, 1, 160.00, 4000.00, 640000.00, '2024-02-18'),
(8, 4, 4, 7, 80.00, 1650.00, 132000.00, '2024-03-01');

-- =============================================================================
-- 10. Insert Retailers (6 Supermarkets & Grocery Stores)
-- =============================================================================
INSERT IGNORE INTO Retailer (retailer_id, retailer_name, phone, address) VALUES
(1, 'FreshVeg Supermart', '9611223344', 'Brigade Road, Bangalore'),
(2, 'Annapurna Grocery Store', '9622334455', 'Laxmi Road, Pune'),
(3, 'DailyNeeds Mega Store', '9633445566', 'Sector 22, Chandigarh'),
(4, 'Krishi Bazaar Outlet', '9644556677', 'Kothapet Fruit Market, Hyderabad'),
(5, 'Green Life Organic Foods', '9655667788', 'Indiranagar 100ft Rd, Bangalore'),
(6, 'Kisan Seva Retail Kendra', '9666778899', 'Old Bus Stand Road, Guntur');

-- =============================================================================
-- 11. Insert Retail Supplies (Distributor -> Retailer)
-- =============================================================================
INSERT IGNORE INTO Retail_Supply (retail_supply_id, distributor_id, retailer_id, crop_id, quantity, price_per_unit, total_price, supply_date) VALUES
(1, 1, 3, 1, 40.00, 4500.00, 180000.00, '2024-01-15'),
(2, 1, 3, 2, 70.00, 2750.00, 192500.00, '2024-04-25'),
(3, 2, 2, 9, 60.00, 2350.00, 141000.00, '2024-02-02'),
(4, 2, 2, 8, 50.00, 1700.00, 85000.00, '2024-03-05'),
(5, 3, 1, 3, 35.00, 3950.00, 138250.00, '2024-02-12'),
(6, 3, 5, 1, 45.00, 4450.00, 200250.00, '2024-03-18'),
(7, 4, 4, 1, 55.00, 4300.00, 236500.00, '2024-02-24'),
(8, 4, 6, 7, 30.00, 1850.00, 55500.00, '2024-03-08');

-- =============================================================================
-- 12. Insert Transport Vehicles (5 Fleet Vehicles)
-- =============================================================================
INSERT IGNORE INTO Vehicle (vehicle_id, vehicle_number, vehicle_type, driver_name, driver_phone) VALUES
(1, 'PB-11-AB-1234', 'Heavy Commercial Truck (16T)', 'Satnam Singh', '9511223344'),
(2, 'MH-12-CD-5678', 'Refrigerated Container Van', 'Ganesh Shinde', '9522334455'),
(3, 'KA-04-EF-9012', 'Medium Freight Truck (10T)', 'Naveen Kumar', '9533445566'),
(4, 'AP-07-GH-3456', 'Multi-Axle Cargo Carrier', 'Ranga Rao', '9544556677'),
(5, 'HR-02-JK-7890', 'Mini Cargo Truck (3.5T)', 'Kuldeep Yadav', '9555667788');

-- =============================================================================
-- 13. Insert Transportation Logs (Shipment tracking)
-- =============================================================================
INSERT IGNORE INTO Transportation (transport_id, vehicle_id, crop_id, source, destination, quantity, transport_date, status) VALUES
(1, 1, 1, 'Patiala APMC Grain Center', 'Central Silo - Ambala', 200.00, '2023-11-16', 'Delivered'),
(2, 2, 7, 'Nashik Onion & Veg Mandi', 'Cold Storage - Pune', 100.00, '2024-01-21', 'Delivered'),
(3, 3, 3, 'Mandya Kisan Agro Center', 'South India Silo - Bangalore', 150.00, '2023-11-03', 'Delivered'),
(4, 4, 1, 'Guntur Mirchi Hub', 'Logistics Hub - Guntur', 250.00, '2023-11-26', 'Delivered'),
(5, 5, 2, 'Karnal Wheat Center', 'Central Silo - Ambala', 280.00, '2024-04-16', 'Delivered'),
(6, 1, 2, 'Central Silo - Ambala', 'DailyNeeds Mega Store, Chandigarh', 70.00, '2024-04-26', 'Delivered'),
(7, 2, 9, 'Cold Storage - Pune', 'Annapurna Grocery, Pune', 60.00, '2024-05-02', 'In Transit'),
(8, 3, 1, 'South India Silo - Bangalore', 'FreshVeg Supermart, Bangalore', 45.00, '2024-05-05', 'Pending');

-- =============================================================================
-- 14. Insert Customers (10 Consumers)
-- =============================================================================
INSERT IGNORE INTO Customer (customer_id, customer_name, phone, address) VALUES
(1, 'Amit Verma', '9411223344', 'Flat 402, Green Valley Apts, Chandigarh'),
(2, 'Priya Nair', '9422334455', 'No. 12, Koramangala 4th Block, Bangalore'),
(3, 'Rajeshwari Devi', '9433445566', 'Bunglow 8, Prabhat Road, Pune'),
(4, 'Sandeep Joshi', '9444556677', 'House 56, Sector 15, Panchkula'),
(5, 'Vikas Mehra', '9455667788', '14/B, Kothrud Main Street, Pune'),
(6, 'Sneha Reddy', '9466778899', 'Plot 88, Jubilee Hills, Hyderabad'),
(7, 'Mohammed Irfan', '9477889900', 'No 21, Richmond Road, Bangalore'),
(8, 'Kavita Patil', '9488990011', 'Flat 101, Aundh Heights, Pune'),
(9, 'Arvind Hegde', '9499001122', '3rd Cross, Malleshwaram, Bangalore'),
(10, 'Deepa Gupta', '9400112233', 'D-204, Guntur Town Centre, AP');

-- =============================================================================
-- 15. Insert Retail Sales (Final Sales to End Customers)
-- =============================================================================
INSERT IGNORE INTO Sales (sale_id, customer_id, retailer_id, crop_id, quantity, price_per_unit, total_price, sale_date) VALUES
(1, 1, 3, 1, 2.00, 5200.00, 10400.00, '2024-01-20'),
(2, 1, 3, 2, 3.00, 3100.00, 9300.00, '2024-05-01'),
(3, 2, 1, 3, 1.50, 4400.00, 6600.00, '2024-02-15'),
(4, 3, 2, 9, 2.50, 2800.00, 7000.00, '2024-02-10'),
(5, 3, 2, 8, 3.00, 2000.00, 6000.00, '2024-03-10'),
(6, 4, 3, 2, 5.00, 3100.00, 15500.00, '2024-05-02'),
(7, 5, 2, 9, 1.00, 2800.00, 2800.00, '2024-02-14'),
(8, 6, 4, 1, 4.00, 4800.00, 19200.00, '2024-03-01'),
(9, 7, 5, 1, 3.00, 5000.00, 15000.00, '2024-03-22'),
(10, 8, 2, 8, 2.00, 2000.00, 4000.00, '2024-03-15'),
(11, 9, 1, 3, 2.00, 4400.00, 8800.00, '2024-02-20'),
(12, 10, 6, 7, 1.50, 2200.00, 3300.00, '2024-03-12');

-- Demo password for every account: AgriChainDemo!2026
-- Hash generated with werkzeug.security.generate_password_hash().
INSERT IGNORE INTO users (username, password_hash, role, entity_id) VALUES
('admin', 'scrypt:32768:8:1$W6nDFyQaCMvM1FCJ$08176ed4aea949ddae6c77f338c1d94d2c52c9463ac9210f9ab91c4539bbfe11da69678556da4cc291dd823a5af5a136b8ba32a0e41979cf1f103420820b6779', 'admin', NULL),
('farmer1', 'scrypt:32768:8:1$oh3OQq0W6flVjkaZ$25f63f5aa1a488264c5972b5b2519336ebf87df1f084ea223a03f84791bb10a92d2f8b60bc991067c9ae5472abeb1fb8a0ab1fb291ba6a340ddfcebb8762c887', 'farmer', 1),
('distributor1', 'scrypt:32768:8:1$GKZOGV82rPsFHcLZ$73ca48d5883c453e25dd2a9d9ce9e106ec175b877825c857dd50bd77def503e30cc74ca8cd38fba5e61bb5709b7baa1daef58d1430303fe416f746527fcabacd', 'distributor', 1),
('retailer1', 'scrypt:32768:8:1$YRxOiQjV6Pu9JdAs$6304c20b92e8c0926237fcd01403bc8139736f8a0aebdfae5a08fb807730d507632748d68c0a9fb7b6f7869d85a5422231c26d393d9b8b3ddb87090be5674b2a', 'retailer', 1),
('customer1', 'scrypt:32768:8:1$dXECGpGyCBKTrdHl$861d4bb559a355adbffbac0c587a399cff1b58b46976c7819127358aa589b5458138a8469666f0d360df0b46975500460270aebf5b69c627b225bc4d6ae0deb1', 'customer', 1);
