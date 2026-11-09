-- =============================================================================
-- Crop Supply Chain Management System
-- DBMS Concepts & Demonstration Queries
-- For College Viva, Lab Demonstrations, and Reports
-- =============================================================================

USE crop_management;

-- =============================================================================
-- 1. INNER JOIN Query (Demonstrates relational joining of 3 related entities)
-- Problem: List all crop supplies with Farmer Name, Crop Name, Collection Center,
--          Quantity, Unit, and Total Amount.
-- =============================================================================
SELECT 
    cs.supply_id,
    f.name AS farmer_name,
    f.village AS farmer_village,
    c.crop_name,
    c.crop_type,
    cc.center_name AS collection_center,
    cs.quantity,
    c.unit,
    cs.price_per_unit,
    cs.total_amount,
    cs.supply_date
FROM Crop_Supply cs
INNER JOIN Farmer f ON cs.farmer_id = f.farmer_id
INNER JOIN Crop c ON cs.crop_id = c.crop_id
INNER JOIN Collection_Center cc ON cs.center_id = cc.center_id
ORDER BY cs.supply_date DESC;

-- =============================================================================
-- 2. LEFT OUTER JOIN Query
-- Problem: List ALL crops in the catalog along with current warehouse stock levels,
--          including crops that have zero current stock.
-- =============================================================================
SELECT 
    c.crop_id,
    c.crop_name,
    c.crop_type,
    c.unit,
    COALESCE(SUM(i.quantity), 0) AS total_inventory_stock
FROM Crop c
LEFT JOIN Inventory i ON c.crop_id = i.crop_id
GROUP BY c.crop_id, c.crop_name, c.crop_type, c.unit
ORDER BY total_inventory_stock DESC;

-- =============================================================================
-- 3. GROUP BY with Aggregate Functions (COUNT, SUM, AVG, MIN, MAX)
-- Problem: Calculate total crop production, average yield, max yield, and total logs per crop.
-- =============================================================================
SELECT 
    c.crop_name,
    COUNT(p.production_id) AS total_production_records,
    SUM(p.quantity) AS total_quantity_produced,
    ROUND(AVG(p.quantity), 2) AS average_production_quantity,
    MIN(p.quantity) AS min_single_yield,
    MAX(p.quantity) AS max_single_yield,
    c.unit
FROM Crop c
INNER JOIN Production p ON c.crop_id = p.crop_id
GROUP BY c.crop_id, c.crop_name, c.unit
ORDER BY total_quantity_produced DESC;

-- =============================================================================
-- 4. GROUP BY with HAVING Clause
-- Problem: Find high-volume farmers who have supplied more than 250 units in total.
-- =============================================================================
SELECT 
    f.farmer_id,
    f.name AS farmer_name,
    f.village,
    COUNT(cs.supply_id) AS number_of_supplies,
    SUM(cs.quantity) AS total_supplied_qty,
    SUM(cs.total_amount) AS total_earnings_inr
FROM Farmer f
JOIN Crop_Supply cs ON f.farmer_id = cs.farmer_id
GROUP BY f.farmer_id, f.name, f.village
HAVING SUM(cs.quantity) >= 250.00
ORDER BY total_supplied_qty DESC;

-- =============================================================================
-- 5. Subqueries (Nested & Correlated Subqueries)
-- Problem A: Find crops whose price per unit in supply is higher than average price of all supplies.
-- =============================================================================
SELECT DISTINCT 
    c.crop_name, 
    cs.price_per_unit, 
    cs.supply_date
FROM Crop_Supply cs
JOIN Crop c ON cs.crop_id = c.crop_id
WHERE cs.price_per_unit > (SELECT AVG(price_per_unit) FROM Crop_Supply)
ORDER BY cs.price_per_unit DESC;

-- Problem B (Correlated Subquery): Find farmers who produced above average for their specific crop.
SELECT 
    f.name AS farmer_name,
    c.crop_name,
    p.quantity,
    p.season
FROM Production p
JOIN Farmer f ON p.farmer_id = f.farmer_id
JOIN Crop c ON p.crop_id = c.crop_id
WHERE p.quantity > (
    SELECT AVG(p2.quantity) 
    FROM Production p2 
    WHERE p2.crop_id = p.crop_id
);

-- =============================================================================
-- 6. Warehouse Occupancy and Low Stock Analysis (Case Statement + Mathematical Expressions)
-- =============================================================================
SELECT 
    w.warehouse_id,
    w.warehouse_name,
    w.location,
    w.capacity,
    COALESCE(SUM(i.quantity), 0) AS current_stock,
    (w.capacity - COALESCE(SUM(i.quantity), 0)) AS vacant_capacity,
    CASE 
        WHEN (COALESCE(SUM(i.quantity), 0) / w.capacity) >= 0.80 THEN 'High Occupancy / Near Full'
        WHEN (COALESCE(SUM(i.quantity), 0) / w.capacity) >= 0.40 THEN 'Moderate Occupancy'
        ELSE 'Low Occupancy / Available Space'
    END AS storage_status
FROM Warehouse w
LEFT JOIN Inventory i ON w.warehouse_id = i.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name, w.location, w.capacity;

-- =============================================================================
-- 7. End-to-End Value Addition Analysis (Supply Chain Price Escalation)
-- Traces price per unit from Farmer -> Distributor -> Retailer -> Customer for Rice
-- =============================================================================
SELECT 
    '1. Farmer Supply to Collection Center' AS stage,
    AVG(price_per_unit) AS avg_price_per_unit
FROM Crop_Supply WHERE crop_id = 1
UNION ALL
SELECT 
    '2. Distributor Purchase from Warehouse' AS stage,
    AVG(price_per_unit) AS avg_price_per_unit
FROM Purchase WHERE crop_id = 1
UNION ALL
SELECT 
    '3. Retailer Supply from Distributor' AS stage,
    AVG(price_per_unit) AS avg_price_per_unit
FROM Retail_Supply WHERE crop_id = 1
UNION ALL
SELECT 
    '4. Consumer Retail Sale' AS stage,
    AVG(price_per_unit) AS avg_price_per_unit
FROM Sales WHERE crop_id = 1;

-- =============================================================================
-- 8. Stored Procedure Invocation
-- =============================================================================
CALL sp_get_farmer_report(1);

-- =============================================================================
-- 9. Transaction Example (Demonstrating ACID Properties)
-- Atomically recording a sale while maintaining transactional integrity.
-- =============================================================================
START TRANSACTION;

-- Insert new sale
INSERT INTO Sales (customer_id, retailer_id, crop_id, quantity, price_per_unit, total_price, sale_date)
VALUES (1, 3, 1, 1.00, 5200.00, 5200.00, CURDATE());

-- Verify and commit
COMMIT;
