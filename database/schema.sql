-- =============================================================================
-- Crop Supply Chain Management System
-- Database Schema Definition (MySQL)
-- DBMS College Project
-- =============================================================================

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS crop_management;
USE crop_management;

-- Safe schema creation: do not drop existing tables or data.
SET FOREIGN_KEY_CHECKS = 0;

-- Note: We intentionally do not drop existing tables or views.
-- This script creates the required tables only if they do not already exist.

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 2. Table Definitions (15 Core Entities with Constraints & 3NF Normalization)
-- =============================================================================

-- Entity 1: Farmer
-- Represents agricultural producers who register in the supply chain.
CREATE TABLE IF NOT EXISTS Farmer (
    farmer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    village VARCHAR(100) NOT NULL,
    registration_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Entity 2: Crop
-- Catalog of crop varieties, classification types, and measurement units.
CREATE TABLE IF NOT EXISTS Crop (
    crop_id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL UNIQUE,
    crop_type VARCHAR(50) NOT NULL,       -- e.g., Cereal, Pulse, Cash Crop, Vegetable, Oilseed
    unit VARCHAR(20) NOT NULL DEFAULT 'Quintal', -- Quintal, Ton, Kg, Bag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Entity 3: Production
-- Tracks agricultural output produced by farmers per season.
CREATE TABLE IF NOT EXISTS Production (
    production_id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    crop_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    production_date DATE NOT NULL,
    season VARCHAR(50) NOT NULL,          -- Kharif, Rabi, Zaid, Year-round
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_prod_quantity CHECK (quantity > 0),
    CONSTRAINT fk_production_farmer FOREIGN KEY (farmer_id) 
        REFERENCES Farmer(farmer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_production_crop FOREIGN KEY (crop_id) 
        REFERENCES Crop(crop_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Entity 4: Collection_Center
-- Physical regional centers where farmers bring harvested crops.
CREATE TABLE IF NOT EXISTS Collection_Center (
    center_id INT AUTO_INCREMENT PRIMARY KEY,
    center_name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(150) NOT NULL,
    manager_name VARCHAR(100) NOT NULL,
    contact VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Entity 5: Crop_Supply
-- Records crops supplied by farmers to collection centers with pricing.
CREATE TABLE IF NOT EXISTS Crop_Supply (
    supply_id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    crop_id INT NOT NULL,
    center_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    price_per_unit DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    supply_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_supply_quantity CHECK (quantity > 0),
    CONSTRAINT chk_supply_price CHECK (price_per_unit >= 0),
    CONSTRAINT chk_supply_total CHECK (total_amount >= 0),
    CONSTRAINT fk_supply_farmer FOREIGN KEY (farmer_id) 
        REFERENCES Farmer(farmer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_supply_crop FOREIGN KEY (crop_id) 
        REFERENCES Crop(crop_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_supply_center FOREIGN KEY (center_id) 
        REFERENCES Collection_Center(center_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Entity 6: Warehouse
-- Large storage facilities for stockpiling and managing crop reserves.
CREATE TABLE IF NOT EXISTS Warehouse (
    warehouse_id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(150) NOT NULL,
    capacity DECIMAL(10,2) NOT NULL,      -- Max storage capacity in crop standard units
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_wh_capacity CHECK (capacity > 0)
) ENGINE=InnoDB;

-- Entity 7: Inventory
-- Live available stock levels of each crop per warehouse.
CREATE TABLE IF NOT EXISTS Inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_id INT NOT NULL,
    crop_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_inv_quantity CHECK (quantity >= 0),
    CONSTRAINT uk_warehouse_crop UNIQUE (warehouse_id, crop_id),
    CONSTRAINT fk_inv_warehouse FOREIGN KEY (warehouse_id) 
        REFERENCES Warehouse(warehouse_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_inv_crop FOREIGN KEY (crop_id) 
        REFERENCES Crop(crop_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Entity 8: Distributor
-- Wholesale buyers who purchase bulk crop stock from warehouses.
CREATE TABLE IF NOT EXISTS Distributor (
    distributor_id INT AUTO_INCREMENT PRIMARY KEY,
    distributor_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Entity 9: Purchase
-- Records wholesale bulk purchases made by distributors from warehouses.
CREATE TABLE IF NOT EXISTS Purchase (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    distributor_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    crop_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    price_per_unit DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    purchase_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_purch_quantity CHECK (quantity > 0),
    CONSTRAINT chk_purch_price CHECK (price_per_unit >= 0),
    CONSTRAINT chk_purch_total CHECK (total_price >= 0),
    CONSTRAINT fk_purch_distributor FOREIGN KEY (distributor_id) 
        REFERENCES Distributor(distributor_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_purch_warehouse FOREIGN KEY (warehouse_id) 
        REFERENCES Warehouse(warehouse_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_purch_crop FOREIGN KEY (crop_id) 
        REFERENCES Crop(crop_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Entity 10: Retailer
-- Local markets, grocery stores, and commercial vendors.
CREATE TABLE IF NOT EXISTS Retailer (
    retailer_id INT AUTO_INCREMENT PRIMARY KEY,
    retailer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Entity 11: Retail_Supply
-- Tracks crop shipments sold and transferred from distributors to retailers.
CREATE TABLE IF NOT EXISTS Retail_Supply (
    retail_supply_id INT AUTO_INCREMENT PRIMARY KEY,
    distributor_id INT NOT NULL,
    retailer_id INT NOT NULL,
    crop_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    price_per_unit DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    supply_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ret_supply_quantity CHECK (quantity > 0),
    CONSTRAINT chk_ret_supply_price CHECK (price_per_unit >= 0),
    CONSTRAINT chk_ret_supply_total CHECK (total_price >= 0),
    CONSTRAINT fk_ret_supply_distributor FOREIGN KEY (distributor_id) 
        REFERENCES Distributor(distributor_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ret_supply_retailer FOREIGN KEY (retailer_id) 
        REFERENCES Retailer(retailer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ret_supply_crop FOREIGN KEY (crop_id) 
        REFERENCES Crop(crop_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Entity 12: Vehicle
-- Fleet vehicles used for inter-node agricultural transportation.
CREATE TABLE IF NOT EXISTS Vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type VARCHAR(50) NOT NULL,       -- Truck, Mini-Truck, Tractor-Trailer, Refrigerated Van
    driver_name VARCHAR(100) NOT NULL,
    driver_phone VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Entity 13: Transportation
-- Shipment logistics tracking origin, destination, quantity, and status.
CREATE TABLE IF NOT EXISTS Transportation (
    transport_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    crop_id INT NOT NULL,
    source VARCHAR(150) NOT NULL,
    destination VARCHAR(150) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    transport_date DATE NOT NULL,
    status ENUM('Pending', 'In Transit', 'Delivered') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_trans_quantity CHECK (quantity > 0),
    CONSTRAINT fk_trans_vehicle FOREIGN KEY (vehicle_id) 
        REFERENCES Vehicle(vehicle_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_trans_crop FOREIGN KEY (crop_id) 
        REFERENCES Crop(crop_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Entity 14: Customer
-- End consumers or buying entities.
CREATE TABLE IF NOT EXISTS Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Entity 15: Sales
-- Final retail transactions between retailers and end customers.
CREATE TABLE IF NOT EXISTS Sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    retailer_id INT NOT NULL,
    crop_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    price_per_unit DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    sale_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_sales_quantity CHECK (quantity > 0),
    CONSTRAINT chk_sales_price CHECK (price_per_unit >= 0),
    CONSTRAINT chk_sales_total CHECK (total_price >= 0),
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) 
        REFERENCES Customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_sales_retailer FOREIGN KEY (retailer_id) 
        REFERENCES Retailer(retailer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_sales_crop FOREIGN KEY (crop_id) 
        REFERENCES Crop(crop_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- A polymorphic entity_id cannot reference four different tables with one SQL
-- foreign key; the users triggers enforce the role-specific target instead.
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'farmer', 'distributor', 'retailer', 'customer') NOT NULL,
    entity_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_users_role_entity (role, entity_id),
    CONSTRAINT chk_users_role_entity CHECK (
        (role = 'admin' AND entity_id IS NULL) OR
        (role <> 'admin' AND entity_id IS NOT NULL)
    )
) ENGINE=InnoDB;

-- =============================================================================
-- 3. SQL Views (DBMS Analytical Reporting)
-- =============================================================================

-- View 1: Crop Stock Summary across all Warehouses
CREATE OR REPLACE VIEW vw_crop_summary AS
SELECT 
    c.crop_id,
    c.crop_name,
    c.crop_type,
    c.unit,
    COALESCE(SUM(i.quantity), 0) AS total_available_stock,
    COUNT(DISTINCT i.warehouse_id) AS stored_in_warehouses_count
FROM Crop c
LEFT JOIN Inventory i ON c.crop_id = i.crop_id
GROUP BY c.crop_id, c.crop_name, c.crop_type, c.unit;

-- View 2: Warehouse Occupancy and Capacity Utilization
CREATE OR REPLACE VIEW vw_warehouse_occupancy AS
SELECT 
    w.warehouse_id,
    w.warehouse_name,
    w.location,
    w.capacity,
    COALESCE(SUM(i.quantity), 0) AS total_occupied,
    (w.capacity - COALESCE(SUM(i.quantity), 0)) AS available_space,
    ROUND((COALESCE(SUM(i.quantity), 0) / w.capacity) * 100, 2) AS utilization_percent
FROM Warehouse w
LEFT JOIN Inventory i ON w.warehouse_id = i.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name, w.location, w.capacity;

-- View 3: Farmer Total Supply and Earnings Overview
CREATE OR REPLACE VIEW vw_farmer_supply_totals AS
SELECT 
    f.farmer_id,
    f.name AS farmer_name,
    f.village,
    f.phone,
    COUNT(cs.supply_id) AS total_supplies_count,
    COALESCE(SUM(cs.quantity), 0) AS total_quantity_supplied,
    COALESCE(SUM(cs.total_amount), 0) AS total_earnings
FROM Farmer f
LEFT JOIN Crop_Supply cs ON f.farmer_id = cs.farmer_id
GROUP BY f.farmer_id, f.name, f.village, f.phone;

-- View 4: Retailer Sales Revenue Summary
CREATE OR REPLACE VIEW vw_retailer_revenue AS
SELECT 
    r.retailer_id,
    r.retailer_name,
    r.phone,
    COUNT(s.sale_id) AS total_sales_count,
    COALESCE(SUM(s.quantity), 0) AS total_quantity_sold,
    COALESCE(SUM(s.total_price), 0) AS total_revenue
FROM Retailer r
LEFT JOIN Sales s ON r.retailer_id = s.retailer_id
GROUP BY r.retailer_id, r.retailer_name, r.phone;

-- =============================================================================
-- 4. Stored Procedures (DBMS Automation)
-- =============================================================================

DELIMITER //

-- Procedure: Get comprehensive summary report for a specific farmer
CREATE PROCEDURE sp_get_farmer_report(IN p_farmer_id INT)
BEGIN
    -- Farmer profile and earnings
    SELECT * FROM vw_farmer_supply_totals WHERE farmer_id = p_farmer_id;
    
    -- Detailed supplies made by this farmer
    SELECT 
        cs.supply_id,
        c.crop_name,
        cc.center_name,
        cs.quantity,
        c.unit,
        cs.price_per_unit,
        cs.total_amount,
        cs.supply_date
    FROM Crop_Supply cs
    JOIN Crop c ON cs.crop_id = c.crop_id
    JOIN Collection_Center cc ON cs.center_id = cc.center_id
    WHERE cs.farmer_id = p_farmer_id
    ORDER BY cs.supply_date DESC;
END //

-- Procedure: Record a new distributor purchase and adjust inventory
CREATE PROCEDURE sp_record_purchase(
    IN p_distributor_id INT,
    IN p_warehouse_id INT,
    IN p_crop_id INT,
    IN p_quantity DECIMAL(10,2),
    IN p_price_per_unit DECIMAL(10,2),
    IN p_purchase_date DATE
)
BEGIN
    DECLARE v_available_stock DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_total_price DECIMAL(12,2);

    -- Calculate total price
    SET v_total_price = p_quantity * p_price_per_unit;

    -- Check current stock in warehouse
    SELECT COALESCE(quantity, 0) INTO v_available_stock
    FROM Inventory
    WHERE warehouse_id = p_warehouse_id AND crop_id = p_crop_id;

    IF v_available_stock >= p_quantity THEN
        -- Insert purchase record
        INSERT INTO Purchase (distributor_id, warehouse_id, crop_id, quantity, price_per_unit, total_price, purchase_date)
        VALUES (p_distributor_id, p_warehouse_id, p_crop_id, p_quantity, p_price_per_unit, v_total_price, p_purchase_date);

        -- Deduct inventory
        UPDATE Inventory
        SET quantity = quantity - p_quantity
        WHERE warehouse_id = p_warehouse_id AND crop_id = p_crop_id;
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient inventory in warehouse for this purchase!';
    END IF;
END //

DELIMITER ;

-- =============================================================================
-- 5. Database Triggers (DBMS Automation & Integrity)
-- =============================================================================

DELIMITER //

-- Trigger: Automatically calculate total amount on Crop_Supply if not already computed
CREATE TRIGGER trg_crop_supply_before_insert
BEFORE INSERT ON Crop_Supply
FOR EACH ROW
BEGIN
    IF NEW.total_amount IS NULL OR NEW.total_amount = 0 THEN
        SET NEW.total_amount = NEW.quantity * NEW.price_per_unit;
    END IF;
END //

-- Trigger: Automatically calculate total price on Purchase before insert
CREATE TRIGGER trg_purchase_before_insert
BEFORE INSERT ON Purchase
FOR EACH ROW
BEGIN
    IF NEW.total_price IS NULL OR NEW.total_price = 0 THEN
        SET NEW.total_price = NEW.quantity * NEW.price_per_unit;
    END IF;
END //

-- Trigger: Automatically calculate total price on Retail_Supply before insert
CREATE TRIGGER trg_retail_supply_before_insert
BEFORE INSERT ON Retail_Supply
FOR EACH ROW
BEGIN
    IF NEW.total_price IS NULL OR NEW.total_price = 0 THEN
        SET NEW.total_price = NEW.quantity * NEW.price_per_unit;
    END IF;
END //

-- Trigger: Automatically calculate total price on Sales before insert
CREATE TRIGGER trg_sales_before_insert
BEFORE INSERT ON Sales
FOR EACH ROW
BEGIN
    IF NEW.total_price IS NULL OR NEW.total_price = 0 THEN
        SET NEW.total_price = NEW.quantity * NEW.price_per_unit;
    END IF;
END //

-- A polymorphic users.entity_id is enforced against the entity table for its role.
CREATE TRIGGER trg_users_validate_entity_before_insert
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
    DECLARE entity_exists INT DEFAULT 0;

    IF NEW.role = 'admin' THEN
        IF NEW.entity_id IS NOT NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Admin users must not have an entity_id';
        END IF;
    ELSEIF NEW.entity_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Non-admin users require an entity_id';
    ELSEIF NEW.role = 'farmer' THEN
        SELECT COUNT(*) INTO entity_exists FROM Farmer WHERE farmer_id = NEW.entity_id;
    ELSEIF NEW.role = 'distributor' THEN
        SELECT COUNT(*) INTO entity_exists FROM Distributor WHERE distributor_id = NEW.entity_id;
    ELSEIF NEW.role = 'retailer' THEN
        SELECT COUNT(*) INTO entity_exists FROM Retailer WHERE retailer_id = NEW.entity_id;
    ELSEIF NEW.role = 'customer' THEN
        SELECT COUNT(*) INTO entity_exists FROM Customer WHERE customer_id = NEW.entity_id;
    END IF;

    IF NEW.role <> 'admin' AND entity_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User entity_id does not exist for the assigned role';
    END IF;
END //

CREATE TRIGGER trg_users_validate_entity_before_update
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    DECLARE entity_exists INT DEFAULT 0;

    IF NEW.role = 'admin' THEN
        IF NEW.entity_id IS NOT NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Admin users must not have an entity_id';
        END IF;
    ELSEIF NEW.entity_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Non-admin users require an entity_id';
    ELSEIF NEW.role = 'farmer' THEN
        SELECT COUNT(*) INTO entity_exists FROM Farmer WHERE farmer_id = NEW.entity_id;
    ELSEIF NEW.role = 'distributor' THEN
        SELECT COUNT(*) INTO entity_exists FROM Distributor WHERE distributor_id = NEW.entity_id;
    ELSEIF NEW.role = 'retailer' THEN
        SELECT COUNT(*) INTO entity_exists FROM Retailer WHERE retailer_id = NEW.entity_id;
    ELSEIF NEW.role = 'customer' THEN
        SELECT COUNT(*) INTO entity_exists FROM Customer WHERE customer_id = NEW.entity_id;
    END IF;

    IF NEW.role <> 'admin' AND entity_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User entity_id does not exist for the assigned role';
    END IF;
END //

DELIMITER ;
