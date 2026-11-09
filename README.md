# Crop Supply Chain Management System (AgriChain)

A complete **College Database Management System (DBMS) Project** built with **Python (Flask)**, **MySQL**, **HTML5/CSS3/JavaScript**, and **Bootstrap 5**.

The system tracks the full agricultural supply chain lifecycle:
$$\text{Farmer} \longrightarrow \text{Crop Production} \longrightarrow \text{Collection Center} \longrightarrow \text{Warehouse} \longrightarrow \text{Distributor} \longrightarrow \text{Retailer} \longrightarrow \text{Customer}$$

---

## 📋 Table of Contents
1. [Project Overview & Objectives](#1-project-overview--objectives)
2. [Key Features & Modules](#2-key-features--modules)
3. [Technology Stack](#3-technology-stack)
4. [Project Folder Structure](#4-project-folder-structure)
5. [Database Architecture & DBMS Concepts](#5-database-architecture--dbms-concepts)
6. [Step-by-Step Installation Guide](#6-step-by-step-installation-guide)
   * [Step 1: Python & Virtual Environment Setup](#step-1-python--virtual-environment-setup)
   * [Step 2: Install Python Packages](#step-2-install-python-packages)
   * [Step 3: MySQL Database Setup & Import](#step-3-mysql-database-setup--import)
   * [Step 4: Configure Database Credentials (.env)](#step-4-configure-database-credentials-env)
   * [Step 5: Run the Flask Web Application](#step-5-run-the-flask-web-application)
7. [Analytical DBMS Reports](#7-analytical-dbms-reports)
8. [Common Errors & Troubleshooting](#8-common-errors--troubleshooting)

---

## 1. Project Overview & Objectives

Agricultural supply chains often suffer from lack of transparency, manual record discrepancies, and fragmented communication between farmers, silos, wholesalers, and retail vendors.

This project delivers a centralized **Relational Database Management System** designed to:
* Register and manage farmers, crop varieties, collection hubs, and storage warehouses.
* Track seasonal harvest yields and farmer procurement pricing.
* Monitor real-time warehouse inventory and capacity utilization.
* Record wholesale distributor purchases and retail shipments.
* Track transportation logistics (Pending, In Transit, Delivered).
* Provide analytical DBMS reports using aggregate functions, subqueries, and multi-table joins.

---

## 2. Key Features & Modules

| Module | Features |
| :--- | :--- |
| **Farmer Management** | Add, View, Edit, Delete farmers. Search by name or village. Validates 10-digit phone numbers. |
| **Crop Catalog** | Manage crop classifications (Cereals, Pulses, Cash Crops, Vegetables) and standard measurement units. |
| **Crop Production** | Record seasonal harvest output per farmer (Kharif, Rabi, Zaid, Year-round). |
| **Collection Centers** | Register APMC market yards, regional mandis, and facility managers. |
| **Crop Supply** | Track farmer produce supplied to collection centers with automated total price calculation. |
| **Warehouses** | Monitor storage capacity, occupied stock, vacant space, and occupancy percentages. |
| **Live Inventory** | Real-time warehouse crop stock levels with low-stock warning indicators. |
| **Distributors** | Wholesale commodity buyer directory and profile management. |
| **Purchases** | Bulk distributor purchases from warehouses with automatic stock deduction. |
| **Retailers** | Manage local supermarkets, grocery stores, and retail vendors. |
| **Retail Supply** | Log shipments dispatched from distributors to retail outlets. |
| **Fleet & Transport** | Fleet vehicle directory (Trucks, Vans) and shipment transit tracking with status pills. |
| **Customers** | Registered retail consumer directory. |
| **Sales** | Final point-of-sale retail transactions to consumers. |
| **11 DBMS Reports** | Dedicated analytical reports with SQL previews for college viva & lab evaluations. |

---

## 3. Technology Stack

* **Backend**: Python 3.8+ & Flask 3.0+
* **Database**: MySQL Server 8.0+ / MariaDB (via `mysql-connector-python` or `pymysql`)
* **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, FontAwesome 6
* **Security**: Parameterized SQL queries preventing SQL Injection attacks

---

## 4. Project Folder Structure

```
crop_supply_chain/
├── app.py                     # Main Flask web application and route controllers
├── config.py                  # Environment & database configuration loader
├── requirements.txt           # Python dependencies list
├── .env.example               # Configuration template
├── .env                       # Local active environment settings
├── README.md                  # Comprehensive project documentation
├── ER_DIAGRAM.md              # ER Specifications & Mermaid Visual Diagram
│
├── database/
│   ├── db.py                  # Database connection helper & query executor
│   ├── schema.sql             # MySQL schema (15 normalized tables, views, procedures, triggers)
│   ├── sample_data.sql        # Realistic Indian agricultural sample data for all entities
│   └── queries.sql            # Ready-to-demo DBMS queries for viva & lab demonstrations
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Responsive base layout with navbar and flash messages
│   ├── index.html             # System introduction and 7-tier flow diagram
│   ├── dashboard.html         # Key metrics, low-stock warnings, recent transactions
│   ├── db_setup.html          # Interactive MySQL connection diagnostics & setup guide
│   ├── farmers.html           # Farmer list & search
│   ├── add_farmer.html        # Register new farmer form
│   ├── edit_farmer.html       # Edit farmer details form
│   ├── crops.html             # Crop catalog view
│   ├── add_crop.html          # Add crop variety form
│   ├── edit_crop.html         # Edit crop form
│   ├── production.html        # Seasonal crop harvest logs
│   ├── add_production.html    # Record harvest form
│   ├── collection_centers.html# Collection centers directory
│   ├── add_collection_center.html # Add collection center form
│   ├── edit_collection_center.html# Edit center form
│   ├── supply.html            # Farmer supply records
│   ├── add_supply.html        # Record farmer supply form
│   ├── warehouses.html        # Warehouse capacity & occupancy table
│   ├── add_warehouse.html     # Add warehouse form
│   ├── edit_warehouse.html    # Edit warehouse form
│   ├── inventory.html         # Live stock inventory view
│   ├── add_inventory.html     # Stock in / adjust inventory form
│   ├── distributors.html      # Wholesale distributors directory
│   ├── add_distributor.html   # Register distributor form
│   ├── edit_distributor.html  # Edit distributor form
│   ├── purchases.html         # Distributor wholesale purchase logs
│   ├── add_purchase.html      # Record wholesale purchase form
│   ├── retailers.html         # Retailers directory
│   ├── add_retailer.html      # Add retailer form
│   ├── edit_retailer.html     # Edit retailer form
│   ├── retail_supply.html     # Distributor -> Retailer supplies
│   ├── add_retail_supply.html # Record retail supply form
│   ├── vehicles.html          # Fleet vehicles directory
│   ├── add_vehicle.html       # Add vehicle form
│   ├── edit_vehicle.html      # Edit vehicle form
│   ├── transportation.html    # Shipment logistics tracking
│   ├── add_transportation.html# Create shipment form
│   ├── edit_transportation.html# Update shipment status form
│   ├── customers.html         # Customers directory
│   ├── add_customer.html      # Add customer form
│   ├── edit_customer.html     # Edit customer form
│   ├── sales.html             # Consumer sales log
│   ├── add_sale.html          # Record retail sale form
│   └── reports.html           # 11 analytical DBMS reports
│
└── static/
    ├── css/
    │   └── style.css          # Custom styling, badges, tables, print layouts
    └── js/
        └── script.js          # Dynamic calculators, live search filter, validations
```

---

## 5. Database Architecture & DBMS Concepts

This project demonstrates the core principles of Database Management Systems:

1. **Entity-Relationship Model**: 15 distinct entities normalized to 3NF.
2. **Key Constraints**:
   * `PRIMARY KEY`: Unique identifier on all tables (`AUTO_INCREMENT`).
   * `FOREIGN KEY`: Referential integrity linking tables with `ON DELETE CASCADE` and `ON DELETE RESTRICT`.
   * `UNIQUE KEY`: Enforces uniqueness on phone numbers, crop names, warehouse-crop pairs.
   * `CHECK Constraint`: Guarantees quantities $> 0$ and prices $\ge 0$.
3. **Multi-Table JOINs**: `INNER JOIN` and `LEFT OUTER JOIN` linking Farmers, Crops, Hubs, and Retailers.
4. **Aggregate Functions**: `SUM()`, `AVG()`, `COUNT()`, `MIN()`, `MAX()` with `GROUP BY` and `HAVING` filters.
5. **Views**: `vw_crop_summary`, `vw_warehouse_occupancy`, `vw_farmer_supply_totals`, `vw_retailer_revenue`.
6. **Stored Procedures**: `sp_get_farmer_report`, `sp_record_purchase`.
7. **Triggers**: Auto total price calculation and inventory deduction upon purchase.
8. **ACID Transactions**: Atomic commit and rollback for multi-table updates.

---

## 6. Step-by-Step Installation Guide

Follow these beginner-friendly steps to set up and run the project:

### Step 1: Python & Virtual Environment Setup

Open PowerShell or Command Prompt in the project directory:

```bash
# 1. Verify Python is installed (should show Python 3.8 or higher)
python --version

# 2. Create a virtual environment (named 'venv')
python -m venv venv

# 3. Activate the virtual environment:
# On Windows:
venv\Scripts\activate
# On macOS / Linux:
# source venv/bin/activate
```

*(When activated, you will see `(venv)` at the beginning of your terminal prompt).*

---

### Step 2: Install Python Packages

Install all required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

---

### Step 3: MySQL Database Setup & Import

You can use **XAMPP (phpMyAdmin)**, **MySQL Workbench**, or the **MySQL Command Line Client**.

#### Method A: Using MySQL Command Line (Fastest)

```bash
# 1. Import database schema (creates database 'crop_management' and all 15 tables)
mysql -u root -p < database/schema.sql

# 2. Import realistic sample data
mysql -u root -p < database/sample_data.sql
```
*(Enter your MySQL root password when prompted).*

#### Method B: Using phpMyAdmin (XAMPP)

1. Open XAMPP Control Panel and click **Start** next to **MySQL** and **Apache**.
2. Open your browser and navigate to: `http://localhost/phpmyadmin`
3. Click on the **Import** tab at the top.
4. Click **Choose File**, select `database/schema.sql`, and click **Go / Import**.
5. Click **Import** again, select `database/sample_data.sql`, and click **Go / Import**.

#### Method C: One-Click Web UI Initializer

Import the schema and sample data once using Method A or B to create the initial admin account. After signing in as `admin`, visit `http://127.0.0.1:5000/db-setup` and click **Run Schema & Sample Data Setup**.

### Role-Based Demo Logins

The sample data creates one account for each role. All demo accounts use password `AgriChainDemo!2026`.

| Role | Username |
| :--- | :--- |
| Administrator | `admin` |
| Farmer | `farmer1` |
| Distributor | `distributor1` |
| Retailer | `retailer1` |
| Customer | `customer1` |

After the initial sign-in, replace demo passwords and configure a strong random `SECRET_KEY` in `.env` before exposing the app outside a development environment. Because `users.entity_id` is polymorphic, the schema triggers and login flow validate it against the table associated with the account role.

---

### Step 4: Configure Database Credentials (.env)

Open the `.env` file in a text editor (e.g., VS Code or Notepad) and configure your MySQL credentials:

```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_NAME=crop_management
SECRET_KEY=replace_with_a_long_random_secret
```

> [!TIP]
> If using **XAMPP**, default `DB_USER` is `root` and `DB_PASSWORD` is empty (leave blank).

---

### Step 5: Run the Flask Web Application

In your terminal with the virtual environment activated:

```bash
python app.py
```

You will see:
```
======================================================================
🌾 Starting Crop Supply Chain Management System...
🌐 Open http://127.0.0.1:5000 in your web browser.
📌 Import schema and sample data first, then sign in using a demo account.
======================================================================
 * Running on http://127.0.0.1:5000
```

Open your browser and visit: **`http://127.0.0.1:5000`**

---

## 7. Analytical DBMS Reports

Navigate to **`http://127.0.0.1:5000/reports`** to view all 11 reports:

1. **Farmer-Wise Crop Supply & Earnings**: Total volume and earnings per farmer (`LEFT JOIN`, `GROUP BY`, `SUM`).
2. **Crop-Wise Harvest Production**: Overall harvest quantities and average yield per crop.
3. **Crop-Wise Available Inventory**: Consolidated stockpile across all state warehouses.
4. **Warehouse Capacity Utilization**: Occupancy percentages and vacant space per warehouse.
5. **Distributor Wholesale Purchases**: Total orders and expenditure per distributor.
6. **Retailer Procurement Supplies**: Dispatches received by retail outlets from distributors.
7. **Logistics & Fleet Status Breakdown**: Shipments grouped by status (`Pending`, `In Transit`, `Delivered`).
8. **Customer Purchases & Sales**: Consumer retail order volume and spending analysis.
9. **Financial Turnover Overview**: End-to-end turnover across all 4 supply chain transactional stages.
10. **Top Supplied Crops**: Crops ranked by supply volume (`ORDER BY total_quantity DESC`).
11. **Low-Stock Inventory Alerts**: Storage facilities with crop levels below the 300 unit threshold.

---

## 8. Common Errors & Troubleshooting

### 1. `Error: Can't connect to MySQL server on 'localhost'`
* **Cause**: MySQL service is not running.
* **Fix**: If using XAMPP, open XAMPP Control Panel and start MySQL. If using Windows MySQL Server, start the MySQL Service from `services.msc`.

### 2. `Access denied for user 'root'@'localhost'`
* **Cause**: Incorrect MySQL password in `.env`.
* **Fix**: Open `.env` and enter your correct MySQL password for `DB_PASSWORD`.

### 3. `ModuleNotFoundError: No module named 'flask'`
* **Cause**: Dependencies not installed or virtual environment not activated.
* **Fix**: Run `venv\Scripts\activate` and then `pip install -r requirements.txt`.

### 4. `Foreign Key Constraint Violation on Delete`
* **Cause**: Attempting to delete an entity (like a crop) referenced by existing inventory or purchase records.
* **Fix**: This is expected relational database behavior (`ON DELETE RESTRICT`) protecting database integrity. Delete dependent transactions first or use Cascade rules.

---

## 👨‍💻 Project Submission Details

* **Project Title**: Crop Supply Chain Management System
* **Domain**: Agricultural Database & Supply Chain Logistics
* **Database**: MySQL (3NF Normalized, 15 Entities)
* **Framework**: Python Flask
