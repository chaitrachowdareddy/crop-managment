"""
=============================================================================
Crop Supply Chain Management System - Main Flask Application
College DBMS Project
Farmer -> Crop Production -> Collection Center -> Warehouse -> Distributor -> Retailer -> Customer
=============================================================================
"""

import os
from functools import wraps
from datetime import date
from flask import Flask, abort, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from config import Config
from database.db import execute_query, test_connection, run_sql_script

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')

ROLE_ENDPOINTS = {
    'index': {'admin', 'farmer', 'distributor', 'retailer', 'customer'},
    'logout': {'admin', 'farmer', 'distributor', 'retailer', 'customer'},
    'dashboard': {'admin', 'farmer', 'distributor', 'retailer', 'customer'},
    'list_farmers': {'admin'},
    'list_crops': {'admin', 'farmer'},
    'list_production': {'admin', 'farmer'},
    'add_production': {'admin', 'farmer'},
    'list_supply': {'admin', 'farmer'},
    'add_supply': {'admin', 'farmer'},
    'list_inventory': {'admin', 'distributor'},
    'list_purchases': {'admin', 'distributor'},
    'add_purchase': {'admin', 'distributor'},
    'list_retail_supplies': {'admin', 'distributor', 'retailer'},
    'add_retail_supply': {'admin', 'distributor'},
    'list_sales': {'admin', 'retailer', 'customer'},
    'add_sale': {'admin', 'retailer'},
    'customer_shop': {'customer'},
    'customer_buy': {'customer'},
    'customer_track': {'customer'},
}


def login_required(view):
    """Redirect users without an authenticated session to the login page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view


def role_required(*allowed_roles):
    """Restrict a view to one or more authenticated roles."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped_view(*args, **kwargs):
            if session.get('role') not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped_view
    return decorator


@app.before_request
def enforce_route_access():
    """Apply authentication by default and deny unlisted endpoints to non-admins."""
    endpoint = request.endpoint
    if endpoint in {'login', 'static'}:
        return None

    if 'user_id' not in session:
        return redirect(url_for('login'))

    allowed_roles = ROLE_ENDPOINTS.get(endpoint)
    if session.get('role') != 'admin' and (
        allowed_roles is None or session.get('role') not in allowed_roles
    ):
        abort(403)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate a user and establish a role-bound session."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Enter your username and password.', 'danger')
            return render_template('login.html')

        try:
            user = safe_query(
                "SELECT user_id, username, password_hash, role, entity_id "
                "FROM users WHERE username = %s;",
                (username,),
                fetchone=True
            )
        except Exception:
            app.logger.exception("Unable to query user credentials")
            flash('Unable to verify login right now. Check database setup and try again.', 'danger')
            return render_template('login.html')

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')

        if user['role'] == 'admin':
            if user['entity_id'] is not None:
                flash('This account has an invalid role assignment.', 'danger')
                return render_template('login.html')
        else:
            entity_tables = {
                'farmer': ('Farmer', 'farmer_id'),
                'distributor': ('Distributor', 'distributor_id'),
                'retailer': ('Retailer', 'retailer_id'),
                'customer': ('Customer', 'customer_id'),
            }
            table, entity_column = entity_tables[user['role']]
            if user['entity_id'] is None or not safe_query(
                f"SELECT {entity_column} FROM {table} WHERE {entity_column} = %s;",
                (user['entity_id'],),
                fetchone=True
            ):
                flash('This account is not linked to an active profile.', 'danger')
                return render_template('login.html')

        session.clear()
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['entity_id'] = user['entity_id']
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear the authenticated session."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.context_processor
def inject_today():
    """Provides current ISO date string to all Jinja templates."""
    return {'today': date.today().isoformat()}


# =============================================================================
# Helper: Database Exception Decorator / Safe Query Runner
# =============================================================================
def safe_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """Executes query and catches connection errors gracefully."""
    try:
        return execute_query(query, params, fetchone=fetchone, fetchall=fetchall, commit=commit)
    except Exception as e:
        app.logger.error(f"Database Query Error: {e}")
        raise e


def get_tracking_status(status):
    """Maps internal logistics states to customer-friendly tracking labels."""
    if status is None:
        return "Ordered"

    clean_status = str(status).strip().lower()
    if clean_status in ('delivered', 'completed', 'done'):
        return 'Delivered'
    if clean_status in ('out for delivery', 'out-for-delivery', 'dispatching', 'dispatched'):
        return 'Out for Delivery'
    if clean_status in ('in transit', 'in_transit', 'transit', 'shipping'):
        return 'In Transit'
    if clean_status in ('pending', 'ordered'):
        return 'Ordered'
    return 'Ordered'


def build_customer_address(address, city=None):
    """Normalizes customer address and city into a single delivery address string."""
    cleaned_address = (address or '').strip()
    cleaned_city = (city or '').strip()

    if cleaned_city and cleaned_address and cleaned_city.lower() not in cleaned_address.lower():
        return f"{cleaned_address}, {cleaned_city}"
    if cleaned_city and not cleaned_address:
        return cleaned_city
    return cleaned_address


def get_estimated_arrival(status):
    """Generates a simple estimated arrival date based on the tracking stage."""
    from datetime import datetime, timedelta

    stage = get_tracking_status(status)
    today = datetime.today().date()

    if stage == 'Delivered':
        return (today - timedelta(days=1)).isoformat()
    if stage == 'Out for Delivery':
        return (today + timedelta(days=1)).isoformat()
    if stage == 'In Transit':
        return (today + timedelta(days=2)).isoformat()
    return (today + timedelta(days=3)).isoformat()


# =============================================================================
# 1. Home & Dashboard Routes
# =============================================================================

@app.route('/')
def index():
    """Send authenticated users to their dashboard."""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Render a dashboard scoped to the authenticated user's role and entity."""
    role = session.get('role')
    entity_id = session.get('entity_id')
    if role != 'admin' and entity_id is None:
        session.clear()
        flash('Your account is not linked to an active profile. Contact an administrator.', 'danger')
        return redirect(url_for('login'))

    if role == 'farmer':
        farmer_id = entity_id
        profile = safe_query(
            "SELECT farmer_id, name, phone, address, village, registration_date "
            "FROM Farmer WHERE farmer_id = %s;",
            (farmer_id,),
            fetchone=True
        )
        production = safe_query("""
            SELECT c.crop_name, c.unit, p.quantity, p.production_date, p.season
            FROM Production p JOIN Crop c ON p.crop_id = c.crop_id
            WHERE p.farmer_id = %s
            ORDER BY p.production_date DESC, p.production_id DESC;
        """, (farmer_id,), fetchall=True)
        supplies = safe_query("""
            SELECT c.crop_name, c.unit, cc.center_name, cs.quantity,
                   cs.price_per_unit, cs.total_amount, cs.supply_date
            FROM Crop_Supply cs
            JOIN Crop c ON cs.crop_id = c.crop_id
            JOIN Collection_Center cc ON cs.center_id = cc.center_id
            WHERE cs.farmer_id = %s
            ORDER BY cs.supply_date DESC, cs.supply_id DESC;
        """, (farmer_id,), fetchall=True)
        earnings = safe_query(
            "SELECT COALESCE(SUM(total_amount), 0) AS total "
            "FROM Crop_Supply WHERE farmer_id = %s;",
            (farmer_id,),
            fetchone=True
        )['total']
        if not profile:
            session.clear()
            flash('Your farm profile is no longer available. Contact an administrator.', 'danger')
            return redirect(url_for('login'))
        return render_template(
            'dashboard_farmer.html',
            profile=profile,
            production=production,
            supplies=supplies,
            earnings=earnings
        )

    if role == 'distributor':
        distributor_id = entity_id
        inventory = safe_query("""
            SELECT w.warehouse_name, c.crop_name, c.unit, i.quantity
            FROM Inventory i
            JOIN Warehouse w ON i.warehouse_id = w.warehouse_id
            JOIN Crop c ON i.crop_id = c.crop_id
            WHERE i.quantity > 0
            ORDER BY w.warehouse_name, c.crop_name;
        """, fetchall=True)
        purchases = safe_query("""
            SELECT w.warehouse_name, c.crop_name, c.unit, p.quantity,
                   p.total_price, p.purchase_date
            FROM Purchase p
            JOIN Warehouse w ON p.warehouse_id = w.warehouse_id
            JOIN Crop c ON p.crop_id = c.crop_id
            WHERE p.distributor_id = %s
            ORDER BY p.purchase_date DESC, p.purchase_id DESC;
        """, (distributor_id,), fetchall=True)
        dispatches = safe_query("""
            SELECT r.retailer_name, c.crop_name, c.unit, rs.quantity,
                   rs.total_price, rs.supply_date
            FROM Retail_Supply rs
            JOIN Retailer r ON rs.retailer_id = r.retailer_id
            JOIN Crop c ON rs.crop_id = c.crop_id
            WHERE rs.distributor_id = %s
            ORDER BY rs.supply_date DESC, rs.retail_supply_id DESC;
        """, (distributor_id,), fetchall=True)
        return render_template(
            'dashboard_distributor.html',
            inventory=inventory,
            purchases=purchases,
            dispatches=dispatches
        )

    if role == 'retailer':
        retailer_id = entity_id
        profile = safe_query(
            "SELECT retailer_id, retailer_name, phone, address "
            "FROM Retailer WHERE retailer_id = %s;",
            (retailer_id,),
            fetchone=True
        )
        stock_received = safe_query("""
            SELECT c.crop_name, c.unit, SUM(rs.quantity) AS quantity_received,
                   SUM(rs.total_price) AS total_cost,
                   SUM(rs.quantity) - COALESCE(MAX(s.quantity_sold), 0) AS quantity_available
            FROM Retail_Supply rs
            JOIN Crop c ON rs.crop_id = c.crop_id
            LEFT JOIN (
                SELECT retailer_id, crop_id, SUM(quantity) AS quantity_sold
                FROM Sales
                GROUP BY retailer_id, crop_id
            ) s ON s.retailer_id = rs.retailer_id AND s.crop_id = rs.crop_id
            WHERE rs.retailer_id = %s
            GROUP BY c.crop_id, c.crop_name, c.unit, s.quantity_sold
            ORDER BY c.crop_name;
        """, (retailer_id,), fetchall=True)
        sales = safe_query("""
            SELECT cu.customer_name, c.crop_name, c.unit, s.quantity,
                   s.total_price, s.sale_date
            FROM Sales s
            JOIN Customer cu ON s.customer_id = cu.customer_id
            JOIN Crop c ON s.crop_id = c.crop_id
            WHERE s.retailer_id = %s
            ORDER BY s.sale_date DESC, s.sale_id DESC;
        """, (retailer_id,), fetchall=True)
        if not profile:
            session.clear()
            flash('Your retailer profile is no longer available. Contact an administrator.', 'danger')
            return redirect(url_for('login'))
        return render_template(
            'dashboard_retailer.html',
            profile=profile,
            stock_received=stock_received,
            sales=sales
        )

    if role == 'customer':
        catalog = get_retail_catalog()
        orders = safe_query("""
            SELECT s.sale_id, c.crop_name, c.unit, r.retailer_name,
                   s.quantity, s.total_price, s.sale_date
            FROM Sales s
            JOIN Crop c ON s.crop_id = c.crop_id
            JOIN Retailer r ON s.retailer_id = r.retailer_id
            WHERE s.customer_id = %s
            ORDER BY s.sale_date DESC, s.sale_id DESC;
        """, (entity_id,), fetchall=True)
        return render_template('dashboard_customer.html', catalog=catalog, orders=orders)

    if role != 'admin':
        session.clear()
        return redirect(url_for('login'))

    is_connected, msg, _ = test_connection()
    if not is_connected:
        flash(f"MySQL is not yet configured: {msg}. Please check the DB Setup page.", "warning")
        return redirect(url_for('db_setup'))

    try:
        # 1. Total counts for key metrics
        stats = {
            'total_farmers': safe_query("SELECT COUNT(*) AS count FROM Farmer;", fetchone=True)['count'],
            'total_crops': safe_query("SELECT COUNT(*) AS count FROM Crop;", fetchone=True)['count'],
            'total_centers': safe_query("SELECT COUNT(*) AS count FROM Collection_Center;", fetchone=True)['count'],
            'total_warehouses': safe_query("SELECT COUNT(*) AS count FROM Warehouse;", fetchone=True)['count'],
            'total_distributors': safe_query("SELECT COUNT(*) AS count FROM Distributor;", fetchone=True)['count'],
            'total_retailers': safe_query("SELECT COUNT(*) AS count FROM Retailer;", fetchone=True)['count'],
            'total_customers': safe_query("SELECT COUNT(*) AS count FROM Customer;", fetchone=True)['count'],
            'total_stock': safe_query("SELECT COALESCE(SUM(quantity), 0) AS total FROM Inventory;", fetchone=True)['total'] or 0.0,
            'total_turnover': safe_query("SELECT COALESCE(SUM(total_price), 0) AS total FROM Sales;", fetchone=True)['total'] or 0.0,
            'inventory_alerts': safe_query("SELECT COUNT(*) AS count FROM Inventory WHERE quantity = 0;", fetchone=True)['count'],
        }

        # 2. Recent Crop Supplies
        recent_supplies = safe_query("""
            SELECT cs.supply_id, f.name AS farmer_name, c.crop_name, c.unit,
                   cc.center_name, cs.quantity, cs.total_amount, cs.supply_date
            FROM Crop_Supply cs
            JOIN Farmer f ON cs.farmer_id = f.farmer_id
            JOIN Crop c ON cs.crop_id = c.crop_id
            JOIN Collection_Center cc ON cs.center_id = cc.center_id
            ORDER BY cs.supply_date DESC, cs.supply_id DESC
            LIMIT 5;
        """, fetchall=True)

        # 3. Active Shipments
        active_transports = safe_query("""
            SELECT t.transport_id, v.vehicle_number, c.crop_name, c.unit,
                   t.source, t.destination, t.quantity, t.status
            FROM Transportation t
            JOIN Vehicle v ON t.vehicle_id = v.vehicle_id
            JOIN Crop c ON t.crop_id = c.crop_id
            ORDER BY t.transport_id DESC
            LIMIT 5;
        """, fetchall=True)

        # 4. Warehouse Stock levels
        stock_levels = safe_query("""
            SELECT w.warehouse_name, c.crop_name, c.unit, i.quantity
            FROM Inventory i
            JOIN Warehouse w ON i.warehouse_id = w.warehouse_id
            JOIN Crop c ON i.crop_id = c.crop_id
            ORDER BY i.quantity ASC
            LIMIT 5;
        """, fetchall=True)

        # 5. Recent Sales
        recent_sales = safe_query("""
            SELECT s.sale_id, cu.customer_name, r.retailer_name, c.crop_name,
                   c.unit, s.quantity, s.total_price
            FROM Sales s
            JOIN Customer cu ON s.customer_id = cu.customer_id
            JOIN Retailer r ON s.retailer_id = r.retailer_id
            JOIN Crop c ON s.crop_id = c.crop_id
            ORDER BY s.sale_date DESC, s.sale_id DESC
            LIMIT 5;
        """, fetchall=True)

        return render_template(
            'dashboard.html',
            stats=stats,
            recent_supplies=recent_supplies,
            active_transports=active_transports,
            stock_levels=stock_levels,
            recent_sales=recent_sales
        )
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('db_setup'))


def get_retail_catalog():
    """Return in-stock retailer offerings after accounting for recorded sales."""
    return safe_query("""
        SELECT c.crop_id, c.crop_name, c.crop_type, c.unit,
               r.retailer_id, r.retailer_name,
               rs.quantity - COALESCE(s.quantity_sold, 0) AS stock_quantity,
               rs.price_per_unit
        FROM (
            SELECT retailer_id, crop_id, SUM(quantity) AS quantity,
                   MAX(price_per_unit) AS price_per_unit
            FROM Retail_Supply
            GROUP BY retailer_id, crop_id
        ) rs
        JOIN Crop c ON rs.crop_id = c.crop_id
        JOIN Retailer r ON rs.retailer_id = r.retailer_id
        LEFT JOIN (
            SELECT retailer_id, crop_id, SUM(quantity) AS quantity_sold
            FROM Sales
            GROUP BY retailer_id, crop_id
        ) s ON s.retailer_id = rs.retailer_id AND s.crop_id = rs.crop_id
        WHERE rs.quantity - COALESCE(s.quantity_sold, 0) > 0
        ORDER BY c.crop_name, r.retailer_name;
    """, fetchall=True)


@app.route('/db-setup')
def db_setup():
    """Database configuration, health diagnostics, and setup tutorial page."""
    is_connected, msg, tables_count = test_connection()
    db_config = Config.get_db_config()
    return render_template(
        'db_setup.html',
        db_status=is_connected,
        db_message=msg,
        tables_count=tables_count,
        db_config=db_config
    )


@app.route('/db-init', methods=['POST'])
def init_db_route():
    """One-click web trigger to execute schema.sql and sample_data.sql."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, 'database', 'schema.sql')
    sample_data_path = os.path.join(base_dir, 'database', 'sample_data.sql')

    success_schema, msg_schema = run_sql_script(schema_path)
    if not success_schema:
        flash(f"Failed to execute schema.sql: {msg_schema}", "danger")
        return redirect(url_for('db_setup'))

    success_data, msg_data = run_sql_script(sample_data_path)
    if not success_data:
        flash(f"Schema created, but sample data failed: {msg_data}", "warning")
    else:
        flash("Database schema and realistic sample data successfully initialized!", "success")

    return redirect(url_for('db_setup'))


# =============================================================================
# 2. Farmer Management Routes (CRUD)
# =============================================================================

@app.route('/farmers')
def list_farmers():
    """View all registered farmers."""
    farmers = safe_query("SELECT * FROM Farmer ORDER BY farmer_id ASC;", fetchall=True)
    return render_template('farmers.html', farmers=farmers)


@app.route('/farmers/add', methods=['GET', 'POST'])
def add_farmer():
    """Add a new farmer."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        village = request.form.get('village', '').strip()
        address = request.form.get('address', '').strip()
        registration_date = request.form.get('registration_date', date.today().isoformat())

        if not name or not phone or not village or not address:
            flash("All fields are required.", "danger")
            return render_template('add_farmer.html')

        try:
            safe_query("""
                INSERT INTO Farmer (name, phone, address, village, registration_date)
                VALUES (%s, %s, %s, %s, %s);
            """, (name, phone, address, village, registration_date), commit=True)
            flash(f"Farmer '{name}' registered successfully!", "success")
            return redirect(url_for('list_farmers'))
        except Exception as e:
            flash(f"Error registering farmer: {str(e)}", "danger")

    return render_template('add_farmer.html')


@app.route('/farmers/edit/<int:farmer_id>', methods=['GET', 'POST'])
def edit_farmer(farmer_id):
    """Edit existing farmer details."""
    farmer = safe_query("SELECT * FROM Farmer WHERE farmer_id = %s;", (farmer_id,), fetchone=True)
    if not farmer:
        flash("Farmer not found.", "danger")
        return redirect(url_for('list_farmers'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        village = request.form.get('village', '').strip()
        address = request.form.get('address', '').strip()
        registration_date = request.form.get('registration_date', farmer['registration_date'])

        try:
            safe_query("""
                UPDATE Farmer
                SET name = %s, phone = %s, address = %s, village = %s, registration_date = %s
                WHERE farmer_id = %s;
            """, (name, phone, address, village, registration_date, farmer_id), commit=True)
            flash(f"Farmer '{name}' updated successfully!", "success")
            return redirect(url_for('list_farmers'))
        except Exception as e:
            flash(f"Error updating farmer: {str(e)}", "danger")

    return render_template('edit_farmer.html', farmer=farmer)


@app.route('/farmers/delete/<int:farmer_id>', methods=['POST'])
def delete_farmer(farmer_id):
    """Delete a farmer."""
    try:
        safe_query("DELETE FROM Farmer WHERE farmer_id = %s;", (farmer_id,), commit=True)
        flash("Farmer deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting farmer: {str(e)}", "danger")
    return redirect(url_for('list_farmers'))


# =============================================================================
# 3. Crop Catalog Management Routes (CRUD)
# =============================================================================

@app.route('/crops')
def list_crops():
    """View all crop varieties."""
    crops = safe_query("SELECT * FROM Crop ORDER BY crop_id ASC;", fetchall=True)
    return render_template('crops.html', crops=crops)


@app.route('/crops/add', methods=['GET', 'POST'])
def add_crop():
    """Add a new crop to the catalog."""
    if request.method == 'POST':
        crop_name = request.form.get('crop_name', '').strip()
        crop_type = request.form.get('crop_type', '').strip()
        unit = request.form.get('unit', 'Quintal').strip()

        if not crop_name or not crop_type:
            flash("Crop name and type are required.", "danger")
            return render_template('add_crop.html')

        try:
            safe_query("""
                INSERT INTO Crop (crop_name, crop_type, unit)
                VALUES (%s, %s, %s);
            """, (crop_name, crop_type, unit), commit=True)
            flash(f"Crop '{crop_name}' added to catalog!", "success")
            return redirect(url_for('list_crops'))
        except Exception as e:
            flash(f"Error adding crop: {str(e)}", "danger")

    return render_template('add_crop.html')


@app.route('/crops/edit/<int:crop_id>', methods=['GET', 'POST'])
def edit_crop(crop_id):
    """Edit crop details."""
    crop = safe_query("SELECT * FROM Crop WHERE crop_id = %s;", (crop_id,), fetchone=True)
    if not crop:
        flash("Crop not found.", "danger")
        return redirect(url_for('list_crops'))

    if request.method == 'POST':
        crop_name = request.form.get('crop_name', '').strip()
        crop_type = request.form.get('crop_type', '').strip()
        unit = request.form.get('unit', 'Quintal').strip()

        try:
            safe_query("""
                UPDATE Crop
                SET crop_name = %s, crop_type = %s, unit = %s
                WHERE crop_id = %s;
            """, (crop_name, crop_type, unit, crop_id), commit=True)
            flash(f"Crop '{crop_name}' updated successfully!", "success")
            return redirect(url_for('list_crops'))
        except Exception as e:
            flash(f"Error updating crop: {str(e)}", "danger")

    return render_template('edit_crop.html', crop=crop)


@app.route('/crops/delete/<int:crop_id>', methods=['POST'])
def delete_crop(crop_id):
    """Delete a crop."""
    try:
        safe_query("DELETE FROM Crop WHERE crop_id = %s;", (crop_id,), commit=True)
        flash("Crop removed from catalog.", "success")
    except Exception as e:
        flash(f"Cannot delete crop (it may have linked production/supply records): {str(e)}", "danger")
    return redirect(url_for('list_crops'))


# =============================================================================
# 4. Crop Production Routes
# =============================================================================

@app.route('/production')
def list_production():
    """View seasonal crop production outputs."""
    query = """
        SELECT p.production_id, f.name AS farmer_name, f.village,
               c.crop_name, c.unit, p.quantity, p.production_date, p.season
        FROM Production p
        JOIN Farmer f ON p.farmer_id = f.farmer_id
        JOIN Crop c ON p.crop_id = c.crop_id
    """
    params = ()
    if session.get('role') == 'farmer':
        query += " WHERE p.farmer_id = %s"
        params = (session['entity_id'],)
    query += " ORDER BY p.production_date DESC, p.production_id DESC;"
    productions = safe_query(query, params, fetchall=True)
    return render_template('production.html', productions=productions)


@app.route('/production/add', methods=['GET', 'POST'])
def add_production():
    """Record a new crop production output."""
    if session.get('role') == 'farmer':
        farmers = safe_query(
            "SELECT farmer_id, name, village FROM Farmer WHERE farmer_id = %s;",
            (session['entity_id'],),
            fetchall=True
        )
    else:
        farmers = safe_query("SELECT farmer_id, name, village FROM Farmer ORDER BY name ASC;", fetchall=True)
    crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)

    if request.method == 'POST':
        farmer_id = session['entity_id'] if session.get('role') == 'farmer' else request.form.get('farmer_id')
        crop_id = request.form.get('crop_id')
        quantity = float(request.form.get('quantity', 0))
        season = request.form.get('season', 'Kharif')
        production_date = request.form.get('production_date', date.today().isoformat())

        if quantity <= 0:
            flash("Quantity must be greater than zero.", "danger")
            return render_template('add_production.html', farmers=farmers, crops=crops)

        try:
            safe_query("""
                INSERT INTO Production (farmer_id, crop_id, quantity, production_date, season)
                VALUES (%s, %s, %s, %s, %s);
            """, (farmer_id, crop_id, quantity, production_date, season), commit=True)
            flash("Crop production output recorded successfully!", "success")
            return redirect(url_for('list_production'))
        except Exception as e:
            flash(f"Error recording production: {str(e)}", "danger")

    return render_template('add_production.html', farmers=farmers, crops=crops)


@app.route('/production/delete/<int:production_id>', methods=['POST'])
def delete_production(production_id):
    """Delete a production record."""
    try:
        safe_query("DELETE FROM Production WHERE production_id = %s;", (production_id,), commit=True)
        flash("Production record deleted.", "success")
    except Exception as e:
        flash(f"Error deleting record: {str(e)}", "danger")
    return redirect(url_for('list_production'))


# =============================================================================
# 5. Collection Center Routes (CRUD)
# =============================================================================

@app.route('/collection-centers')
def list_collection_centers():
    """View all collection centers."""
    centers = safe_query("SELECT * FROM Collection_Center ORDER BY center_id ASC;", fetchall=True)
    return render_template('collection_centers.html', centers=centers)


@app.route('/collection-centers/add', methods=['GET', 'POST'])
def add_collection_center():
    """Add a new collection center."""
    if request.method == 'POST':
        center_name = request.form.get('center_name', '').strip()
        location = request.form.get('location', '').strip()
        manager_name = request.form.get('manager_name', '').strip()
        contact = request.form.get('contact', '').strip()

        try:
            safe_query("""
                INSERT INTO Collection_Center (center_name, location, manager_name, contact)
                VALUES (%s, %s, %s, %s);
            """, (center_name, location, manager_name, contact), commit=True)
            flash(f"Collection Center '{center_name}' created!", "success")
            return redirect(url_for('list_collection_centers'))
        except Exception as e:
            flash(f"Error creating center: {str(e)}", "danger")

    return render_template('add_collection_center.html')


@app.route('/collection-centers/edit/<int:center_id>', methods=['GET', 'POST'])
def edit_collection_center(center_id):
    """Edit collection center."""
    center = safe_query("SELECT * FROM Collection_Center WHERE center_id = %s;", (center_id,), fetchone=True)
    if not center:
        flash("Collection Center not found.", "danger")
        return redirect(url_for('list_collection_centers'))

    if request.method == 'POST':
        center_name = request.form.get('center_name', '').strip()
        location = request.form.get('location', '').strip()
        manager_name = request.form.get('manager_name', '').strip()
        contact = request.form.get('contact', '').strip()

        try:
            safe_query("""
                UPDATE Collection_Center
                SET center_name = %s, location = %s, manager_name = %s, contact = %s
                WHERE center_id = %s;
            """, (center_name, location, manager_name, contact, center_id), commit=True)
            flash(f"Collection Center '{center_name}' updated!", "success")
            return redirect(url_for('list_collection_centers'))
        except Exception as e:
            flash(f"Error updating center: {str(e)}", "danger")

    return render_template('edit_collection_center.html', center=center)


@app.route('/collection-centers/delete/<int:center_id>', methods=['POST'])
def delete_collection_center(center_id):
    """Delete collection center."""
    try:
        safe_query("DELETE FROM Collection_Center WHERE center_id = %s;", (center_id,), commit=True)
        flash("Collection center removed.", "success")
    except Exception as e:
        flash(f"Error deleting center: {str(e)}", "danger")
    return redirect(url_for('list_collection_centers'))


# =============================================================================
# 6. Crop Supply Routes (Farmer -> Collection Center)
# =============================================================================

@app.route('/supply')
def list_supply():
    """View farmer crop supply records."""
    query = """
        SELECT cs.supply_id, f.name AS farmer_name, c.crop_name, c.unit,
               cc.center_name, cs.quantity, cs.price_per_unit, cs.total_amount, cs.supply_date
        FROM Crop_Supply cs
        JOIN Farmer f ON cs.farmer_id = f.farmer_id
        JOIN Crop c ON cs.crop_id = c.crop_id
        JOIN Collection_Center cc ON cs.center_id = cc.center_id
    """
    params = ()
    if session.get('role') == 'farmer':
        query += " WHERE cs.farmer_id = %s"
        params = (session['entity_id'],)
    query += " ORDER BY cs.supply_date DESC, cs.supply_id DESC;"
    supplies = safe_query(query, params, fetchall=True)
    return render_template('supply.html', supplies=supplies)


@app.route('/supply/add', methods=['GET', 'POST'])
def add_supply():
    """Record crop supply from farmer to collection center."""
    if session.get('role') == 'farmer':
        farmers = safe_query(
            "SELECT farmer_id, name, village FROM Farmer WHERE farmer_id = %s;",
            (session['entity_id'],),
            fetchall=True
        )
    else:
        farmers = safe_query("SELECT farmer_id, name, village FROM Farmer ORDER BY name ASC;", fetchall=True)
    crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)
    centers = safe_query("SELECT center_id, center_name, location FROM Collection_Center ORDER BY center_name ASC;", fetchall=True)

    if request.method == 'POST':
        farmer_id = session['entity_id'] if session.get('role') == 'farmer' else request.form.get('farmer_id')
        crop_id = request.form.get('crop_id')
        center_id = request.form.get('center_id')
        quantity = float(request.form.get('quantity', 0))
        price_per_unit = float(request.form.get('price_per_unit', 0))
        supply_date = request.form.get('supply_date', date.today().isoformat())
        total_amount = quantity * price_per_unit

        if quantity <= 0 or price_per_unit < 0:
            flash("Invalid quantity or price.", "danger")
            return render_template('add_supply.html', farmers=farmers, crops=crops, centers=centers)

        try:
            safe_query("""
                INSERT INTO Crop_Supply (farmer_id, crop_id, center_id, quantity, price_per_unit, total_amount, supply_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (farmer_id, crop_id, center_id, quantity, price_per_unit, total_amount, supply_date), commit=True)
            flash(f"Crop supply of {quantity} units recorded successfully!", "success")
            return redirect(url_for('list_supply'))
        except Exception as e:
            flash(f"Error recording supply: {str(e)}", "danger")

    return render_template('add_supply.html', farmers=farmers, crops=crops, centers=centers)


@app.route('/supply/delete/<int:supply_id>', methods=['POST'])
def delete_supply(supply_id):
    """Delete a supply record."""
    try:
        safe_query("DELETE FROM Crop_Supply WHERE supply_id = %s;", (supply_id,), commit=True)
        flash("Supply record deleted.", "success")
    except Exception as e:
        flash(f"Error deleting record: {str(e)}", "danger")
    return redirect(url_for('list_supply'))


# =============================================================================
# 7. Warehouse & Inventory Management Routes
# =============================================================================

@app.route('/warehouses')
def list_warehouses():
    """View warehouses and capacity utilization."""
    warehouses = safe_query("""
        SELECT w.warehouse_id, w.warehouse_name, w.location, w.capacity,
               COALESCE(SUM(i.quantity), 0) AS total_occupied,
               (w.capacity - COALESCE(SUM(i.quantity), 0)) AS available_space,
               ROUND((COALESCE(SUM(i.quantity), 0) / w.capacity) * 100, 2) AS utilization_percent
        FROM Warehouse w
        LEFT JOIN Inventory i ON w.warehouse_id = i.warehouse_id
        GROUP BY w.warehouse_id, w.warehouse_name, w.location, w.capacity
        ORDER BY w.warehouse_id ASC;
    """, fetchall=True)
    return render_template('warehouses.html', warehouses=warehouses)


@app.route('/warehouses/add', methods=['GET', 'POST'])
def add_warehouse():
    """Add a new warehouse facility."""
    if request.method == 'POST':
        warehouse_name = request.form.get('warehouse_name', '').strip()
        location = request.form.get('location', '').strip()
        capacity = float(request.form.get('capacity', 0))

        if capacity <= 0:
            flash("Warehouse capacity must be positive.", "danger")
            return render_template('add_warehouse.html')

        try:
            safe_query("""
                INSERT INTO Warehouse (warehouse_name, location, capacity)
                VALUES (%s, %s, %s);
            """, (warehouse_name, location, capacity), commit=True)
            flash(f"Warehouse '{warehouse_name}' created!", "success")
            return redirect(url_for('list_warehouses'))
        except Exception as e:
            flash(f"Error adding warehouse: {str(e)}", "danger")

    return render_template('add_warehouse.html')


@app.route('/warehouses/edit/<int:warehouse_id>', methods=['GET', 'POST'])
def edit_warehouse(warehouse_id):
    """Edit warehouse details."""
    warehouse = safe_query("SELECT * FROM Warehouse WHERE warehouse_id = %s;", (warehouse_id,), fetchone=True)
    if not warehouse:
        flash("Warehouse not found.", "danger")
        return redirect(url_for('list_warehouses'))

    if request.method == 'POST':
        warehouse_name = request.form.get('warehouse_name', '').strip()
        location = request.form.get('location', '').strip()
        capacity = float(request.form.get('capacity', warehouse['capacity']))

        try:
            safe_query("""
                UPDATE Warehouse
                SET warehouse_name = %s, location = %s, capacity = %s
                WHERE warehouse_id = %s;
            """, (warehouse_name, location, capacity, warehouse_id), commit=True)
            flash(f"Warehouse '{warehouse_name}' updated!", "success")
            return redirect(url_for('list_warehouses'))
        except Exception as e:
            flash(f"Error updating warehouse: {str(e)}", "danger")

    return render_template('edit_warehouse.html', warehouse=warehouse)


@app.route('/warehouses/delete/<int:warehouse_id>', methods=['POST'])
def delete_warehouse(warehouse_id):
    """Delete a warehouse."""
    try:
        safe_query("DELETE FROM Warehouse WHERE warehouse_id = %s;", (warehouse_id,), commit=True)
        flash("Warehouse deleted.", "success")
    except Exception as e:
        flash(f"Error deleting warehouse: {str(e)}", "danger")
    return redirect(url_for('list_warehouses'))


@app.route('/inventory')
def list_inventory():
    """View live inventory stock across warehouses."""
    inventory = safe_query("""
        SELECT i.inventory_id, w.warehouse_name, c.crop_name, c.crop_type,
               c.unit, i.quantity, i.last_updated
        FROM Inventory i
        JOIN Warehouse w ON i.warehouse_id = w.warehouse_id
        JOIN Crop c ON i.crop_id = c.crop_id
        ORDER BY w.warehouse_name ASC, i.quantity DESC;
    """, fetchall=True)
    return render_template('inventory.html', inventory=inventory)


@app.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory():
    """Stock in or adjust warehouse inventory."""
    warehouses = safe_query("SELECT warehouse_id, warehouse_name, capacity FROM Warehouse ORDER BY warehouse_name ASC;", fetchall=True)
    crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)

    if request.method == 'POST':
        warehouse_id = request.form.get('warehouse_id')
        crop_id = request.form.get('crop_id')
        quantity = float(request.form.get('quantity', 0))

        if quantity < 0:
            flash("Quantity cannot be negative.", "danger")
            return render_template('add_inventory.html', warehouses=warehouses, crops=crops)

        try:
            safe_query("""
                INSERT INTO Inventory (warehouse_id, crop_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = %s, last_updated = CURRENT_TIMESTAMP;
            """, (warehouse_id, crop_id, quantity, quantity), commit=True)
            flash("Warehouse inventory updated successfully!", "success")
            return redirect(url_for('list_inventory'))
        except Exception as e:
            flash(f"Error updating inventory: {str(e)}", "danger")

    return render_template('add_inventory.html', warehouses=warehouses, crops=crops)


@app.route('/inventory/delete/<int:inventory_id>', methods=['POST'])
def delete_inventory(inventory_id):
    """Remove inventory record."""
    try:
        safe_query("DELETE FROM Inventory WHERE inventory_id = %s;", (inventory_id,), commit=True)
        flash("Inventory record deleted.", "success")
    except Exception as e:
        flash(f"Error deleting inventory: {str(e)}", "danger")
    return redirect(url_for('list_inventory'))


# =============================================================================
# 8. Distributor Management & Purchases
# =============================================================================

@app.route('/distributors')
def list_distributors():
    """View wholesale distributors."""
    distributors = safe_query("SELECT * FROM Distributor ORDER BY distributor_id ASC;", fetchall=True)
    return render_template('distributors.html', distributors=distributors)


@app.route('/distributors/add', methods=['GET', 'POST'])
def add_distributor():
    """Add a new distributor."""
    if request.method == 'POST':
        distributor_name = request.form.get('distributor_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        try:
            safe_query("""
                INSERT INTO Distributor (distributor_name, phone, address)
                VALUES (%s, %s, %s);
            """, (distributor_name, phone, address), commit=True)
            flash(f"Distributor '{distributor_name}' registered!", "success")
            return redirect(url_for('list_distributors'))
        except Exception as e:
            flash(f"Error adding distributor: {str(e)}", "danger")

    return render_template('add_distributor.html')


@app.route('/distributors/edit/<int:distributor_id>', methods=['GET', 'POST'])
def edit_distributor(distributor_id):
    """Edit distributor profile."""
    distributor = safe_query("SELECT * FROM Distributor WHERE distributor_id = %s;", (distributor_id,), fetchone=True)
    if not distributor:
        flash("Distributor not found.", "danger")
        return redirect(url_for('list_distributors'))

    if request.method == 'POST':
        distributor_name = request.form.get('distributor_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        try:
            safe_query("""
                UPDATE Distributor
                SET distributor_name = %s, phone = %s, address = %s
                WHERE distributor_id = %s;
            """, (distributor_name, phone, address, distributor_id), commit=True)
            flash(f"Distributor '{distributor_name}' updated!", "success")
            return redirect(url_for('list_distributors'))
        except Exception as e:
            flash(f"Error updating distributor: {str(e)}", "danger")

    return render_template('edit_distributor.html', distributor=distributor)


@app.route('/distributors/delete/<int:distributor_id>', methods=['POST'])
def delete_distributor(distributor_id):
    """Delete distributor."""
    try:
        safe_query("DELETE FROM Distributor WHERE distributor_id = %s;", (distributor_id,), commit=True)
        flash("Distributor deleted.", "success")
    except Exception as e:
        flash(f"Error deleting distributor: {str(e)}", "danger")
    return redirect(url_for('list_distributors'))


@app.route('/purchases')
def list_purchases():
    """View distributor purchases from warehouses."""
    query = """
        SELECT p.purchase_id, d.distributor_name, w.warehouse_name,
               c.crop_name, c.unit, p.quantity, p.price_per_unit, p.total_price, p.purchase_date
        FROM Purchase p
        JOIN Distributor d ON p.distributor_id = d.distributor_id
        JOIN Warehouse w ON p.warehouse_id = w.warehouse_id
        JOIN Crop c ON p.crop_id = c.crop_id
    """
    params = ()
    if session.get('role') == 'distributor':
        query += " WHERE p.distributor_id = %s"
        params = (session['entity_id'],)
    query += " ORDER BY p.purchase_date DESC, p.purchase_id DESC;"
    purchases = safe_query(query, params, fetchall=True)
    return render_template('purchases.html', purchases=purchases)


@app.route('/purchases/add', methods=['GET', 'POST'])
def add_purchase():
    """Record wholesale purchase by distributor."""
    if session.get('role') == 'distributor':
        distributors = safe_query(
            "SELECT distributor_id, distributor_name FROM Distributor WHERE distributor_id = %s;",
            (session['entity_id'],),
            fetchall=True
        )
    else:
        distributors = safe_query("SELECT distributor_id, distributor_name FROM Distributor ORDER BY distributor_name ASC;", fetchall=True)
    warehouses = safe_query("SELECT warehouse_id, warehouse_name FROM Warehouse ORDER BY warehouse_name ASC;", fetchall=True)
    crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)

    if request.method == 'POST':
        distributor_id = session['entity_id'] if session.get('role') == 'distributor' else request.form.get('distributor_id')
        warehouse_id = request.form.get('warehouse_id')
        crop_id = request.form.get('crop_id')
        quantity = float(request.form.get('quantity', 0))
        price_per_unit = float(request.form.get('price_per_unit', 0))
        purchase_date = request.form.get('purchase_date', date.today().isoformat())
        total_price = quantity * price_per_unit

        if quantity <= 0 or price_per_unit < 0:
            flash("Quantity and price must be valid positive numbers.", "danger")
            return render_template('add_purchase.html', distributors=distributors, warehouses=warehouses, crops=crops)

        try:
            # Check warehouse stock
            stock = safe_query("""
                SELECT quantity FROM Inventory
                WHERE warehouse_id = %s AND crop_id = %s;
            """, (warehouse_id, crop_id), fetchone=True)

            available = stock['quantity'] if stock else 0
            if available < quantity:
                flash(f"Warning: Warehouse only has {available} units in stock. Purchase cannot exceed available inventory!", "danger")
                return render_template('add_purchase.html', distributors=distributors, warehouses=warehouses, crops=crops)

            # Insert purchase record
            safe_query("""
                INSERT INTO Purchase (distributor_id, warehouse_id, crop_id, quantity, price_per_unit, total_price, purchase_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (distributor_id, warehouse_id, crop_id, quantity, price_per_unit, total_price, purchase_date), commit=True)

            # Deduct inventory atomically
            safe_query("""
                UPDATE Inventory
                SET quantity = quantity - %s
                WHERE warehouse_id = %s AND crop_id = %s;
            """, (quantity, warehouse_id, crop_id), commit=True)

            flash("Distributor purchase order logged and warehouse stock updated!", "success")
            return redirect(url_for('list_purchases'))
        except Exception as e:
            flash(f"Error executing purchase: {str(e)}", "danger")

    return render_template('add_purchase.html', distributors=distributors, warehouses=warehouses, crops=crops)


@app.route('/purchases/delete/<int:purchase_id>', methods=['POST'])
def delete_purchase(purchase_id):
    """Delete a purchase record."""
    try:
        safe_query("DELETE FROM Purchase WHERE purchase_id = %s;", (purchase_id,), commit=True)
        flash("Purchase record deleted.", "success")
    except Exception as e:
        flash(f"Error deleting purchase: {str(e)}", "danger")
    return redirect(url_for('list_purchases'))


# =============================================================================
# 9. Retailer Management & Retail Supply
# =============================================================================

@app.route('/retailers')
def list_retailers():
    """View registered retailers."""
    retailers = safe_query("SELECT * FROM Retailer ORDER BY retailer_id ASC;", fetchall=True)
    return render_template('retailers.html', retailers=retailers)


@app.route('/retailers/add', methods=['GET', 'POST'])
def add_retailer():
    """Add a new retailer."""
    if request.method == 'POST':
        retailer_name = request.form.get('retailer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        try:
            safe_query("""
                INSERT INTO Retailer (retailer_name, phone, address)
                VALUES (%s, %s, %s);
            """, (retailer_name, phone, address), commit=True)
            flash(f"Retailer '{retailer_name}' added!", "success")
            return redirect(url_for('list_retailers'))
        except Exception as e:
            flash(f"Error adding retailer: {str(e)}", "danger")

    return render_template('add_retailer.html')


@app.route('/retailers/edit/<int:retailer_id>', methods=['GET', 'POST'])
def edit_retailer(retailer_id):
    """Edit retailer."""
    retailer = safe_query("SELECT * FROM Retailer WHERE retailer_id = %s;", (retailer_id,), fetchone=True)
    if not retailer:
        flash("Retailer not found.", "danger")
        return redirect(url_for('list_retailers'))

    if request.method == 'POST':
        retailer_name = request.form.get('retailer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        try:
            safe_query("""
                UPDATE Retailer
                SET retailer_name = %s, phone = %s, address = %s
                WHERE retailer_id = %s;
            """, (retailer_name, phone, address, retailer_id), commit=True)
            flash(f"Retailer '{retailer_name}' updated!", "success")
            return redirect(url_for('list_retailers'))
        except Exception as e:
            flash(f"Error updating retailer: {str(e)}", "danger")

    return render_template('edit_retailer.html', retailer=retailer)


@app.route('/retailers/delete/<int:retailer_id>', methods=['POST'])
def delete_retailer(retailer_id):
    """Delete a retailer."""
    try:
        safe_query("DELETE FROM Retailer WHERE retailer_id = %s;", (retailer_id,), commit=True)
        flash("Retailer deleted.", "success")
    except Exception as e:
        flash(f"Error deleting retailer: {str(e)}", "danger")
    return redirect(url_for('list_retailers'))


@app.route('/retail-supplies')
def list_retail_supplies():
    """View retail supplies (Distributor -> Retailer)."""
    query = """
        SELECT rs.retail_supply_id, d.distributor_name, r.retailer_name,
               c.crop_name, c.unit, rs.quantity, rs.price_per_unit, rs.total_price, rs.supply_date
        FROM Retail_Supply rs
        JOIN Distributor d ON rs.distributor_id = d.distributor_id
        JOIN Retailer r ON rs.retailer_id = r.retailer_id
        JOIN Crop c ON rs.crop_id = c.crop_id
    """
    params = ()
    if session.get('role') == 'distributor':
        query += " WHERE rs.distributor_id = %s"
        params = (session['entity_id'],)
    elif session.get('role') == 'retailer':
        query += " WHERE rs.retailer_id = %s"
        params = (session['entity_id'],)
    query += " ORDER BY rs.supply_date DESC, rs.retail_supply_id DESC;"
    retail_supplies = safe_query(query, params, fetchall=True)
    return render_template('retail_supply.html', retail_supplies=retail_supplies)


@app.route('/retail-supplies/add', methods=['GET', 'POST'])
def add_retail_supply():
    """Record retail supply dispatch."""
    if session.get('role') == 'distributor':
        distributors = safe_query(
            "SELECT distributor_id, distributor_name FROM Distributor WHERE distributor_id = %s;",
            (session['entity_id'],),
            fetchall=True
        )
    else:
        distributors = safe_query("SELECT distributor_id, distributor_name FROM Distributor ORDER BY distributor_name ASC;", fetchall=True)
    retailers = safe_query("SELECT retailer_id, retailer_name, address FROM Retailer ORDER BY retailer_name ASC;", fetchall=True)
    crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)

    if request.method == 'POST':
        distributor_id = session['entity_id'] if session.get('role') == 'distributor' else request.form.get('distributor_id')
        retailer_id = request.form.get('retailer_id')
        crop_id = request.form.get('crop_id')
        try:
            quantity = float(request.form.get('quantity', 0))
            price_per_unit = float(request.form.get('price_per_unit', 0))
        except (TypeError, ValueError):
            quantity = 0
            price_per_unit = -1
        supply_date = request.form.get('supply_date', date.today().isoformat())
        total_price = quantity * price_per_unit

        if quantity <= 0 or price_per_unit < 0:
            flash("Quantity must be positive and price must be non-negative.", "danger")
            return render_template('add_retail_supply.html', distributors=distributors, retailers=retailers, crops=crops)
        if session.get('role') == 'distributor':
            remaining_stock = safe_query("""
                SELECT COALESCE(SUM(p.quantity), 0) - COALESCE((
                    SELECT SUM(rs.quantity)
                    FROM Retail_Supply rs
                    WHERE rs.distributor_id = p.distributor_id AND rs.crop_id = p.crop_id
                ), 0) AS available
                FROM Purchase p
                WHERE p.distributor_id = %s AND p.crop_id = %s
                GROUP BY p.distributor_id, p.crop_id;
            """, (distributor_id, crop_id), fetchone=True)
            if not remaining_stock or remaining_stock['available'] < quantity:
                flash("Dispatch quantity exceeds your purchased stock for this crop.", "danger")
                return render_template('add_retail_supply.html', distributors=distributors, retailers=retailers, crops=crops)

        try:
            safe_query("""
                INSERT INTO Retail_Supply (distributor_id, retailer_id, crop_id, quantity, price_per_unit, total_price, supply_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (distributor_id, retailer_id, crop_id, quantity, price_per_unit, total_price, supply_date), commit=True)
            flash("Retail supply dispatch logged successfully!", "success")
            return redirect(url_for('list_retail_supplies'))
        except Exception as e:
            flash(f"Error logging retail supply: {str(e)}", "danger")

    return render_template('add_retail_supply.html', distributors=distributors, retailers=retailers, crops=crops)


@app.route('/retail-supplies/delete/<int:retail_supply_id>', methods=['POST'])
def delete_retail_supply(retail_supply_id):
    """Delete a retail supply record."""
    try:
        safe_query("DELETE FROM Retail_Supply WHERE retail_supply_id = %s;", (retail_supply_id,), commit=True)
        flash("Retail supply record deleted.", "success")
    except Exception as e:
        flash(f"Error deleting record: {str(e)}", "danger")
    return redirect(url_for('list_retail_supplies'))


# =============================================================================
# 10. Vehicle & Transportation Logistics Routes
# =============================================================================

@app.route('/vehicles')
def list_vehicles():
    """View fleet vehicles."""
    vehicles = safe_query("SELECT * FROM Vehicle ORDER BY vehicle_id ASC;", fetchall=True)
    return render_template('vehicles.html', vehicles=vehicles)


@app.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    """Add a new transport vehicle."""
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number', '').strip()
        vehicle_type = request.form.get('vehicle_type', '').strip()
        driver_name = request.form.get('driver_name', '').strip()
        driver_phone = request.form.get('driver_phone', '').strip()

        try:
            safe_query("""
                INSERT INTO Vehicle (vehicle_number, vehicle_type, driver_name, driver_phone)
                VALUES (%s, %s, %s, %s);
            """, (vehicle_number, vehicle_type, driver_name, driver_phone), commit=True)
            flash(f"Vehicle '{vehicle_number}' added to fleet!", "success")
            return redirect(url_for('list_vehicles'))
        except Exception as e:
            flash(f"Error adding vehicle: {str(e)}", "danger")

    return render_template('add_vehicle.html')


@app.route('/vehicles/edit/<int:vehicle_id>', methods=['GET', 'POST'])
def edit_vehicle(vehicle_id):
    """Edit vehicle details."""
    vehicle = safe_query("SELECT * FROM Vehicle WHERE vehicle_id = %s;", (vehicle_id,), fetchone=True)
    if not vehicle:
        flash("Vehicle not found.", "danger")
        return redirect(url_for('list_vehicles'))

    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number', '').strip()
        vehicle_type = request.form.get('vehicle_type', '').strip()
        driver_name = request.form.get('driver_name', '').strip()
        driver_phone = request.form.get('driver_phone', '').strip()

        try:
            safe_query("""
                UPDATE Vehicle
                SET vehicle_number = %s, vehicle_type = %s, driver_name = %s, driver_phone = %s
                WHERE vehicle_id = %s;
            """, (vehicle_number, vehicle_type, driver_name, driver_phone, vehicle_id), commit=True)
            flash(f"Vehicle '{vehicle_number}' updated!", "success")
            return redirect(url_for('list_vehicles'))
        except Exception as e:
            flash(f"Error updating vehicle: {str(e)}", "danger")

    return render_template('edit_vehicle.html', vehicle=vehicle)


@app.route('/vehicles/delete/<int:vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id):
    """Delete a vehicle."""
    try:
        safe_query("DELETE FROM Vehicle WHERE vehicle_id = %s;", (vehicle_id,), commit=True)
        flash("Vehicle removed from fleet.", "success")
    except Exception as e:
        flash(f"Error deleting vehicle: {str(e)}", "danger")
    return redirect(url_for('list_vehicles'))


@app.route('/transportation')
def list_transportation():
    """View shipment transport logs."""
    transportations = safe_query("""
        SELECT t.transport_id, v.vehicle_number, v.driver_name, v.driver_phone,
               c.crop_name, c.unit, t.source, t.destination, t.quantity, t.transport_date, t.status
        FROM Transportation t
        JOIN Vehicle v ON t.vehicle_id = v.vehicle_id
        JOIN Crop c ON t.crop_id = c.crop_id
        ORDER BY t.transport_date DESC, t.transport_id DESC;
    """, fetchall=True)
    return render_template('transportation.html', transportations=transportations)


@app.route('/transportation/add', methods=['GET', 'POST'])
def add_transportation():
    """Create a new transportation shipment."""
    vehicles = safe_query("SELECT vehicle_id, vehicle_number, driver_name, vehicle_type FROM Vehicle ORDER BY vehicle_number ASC;", fetchall=True)
    crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)

    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id')
        crop_id = request.form.get('crop_id')
        source = request.form.get('source', '').strip()
        destination = request.form.get('destination', '').strip()
        quantity = float(request.form.get('quantity', 0))
        transport_date = request.form.get('transport_date', date.today().isoformat())
        status = request.form.get('status', 'Pending')

        try:
            safe_query("""
                INSERT INTO Transportation (vehicle_id, crop_id, source, destination, quantity, transport_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (vehicle_id, crop_id, source, destination, quantity, transport_date, status), commit=True)
            flash("Transport shipment created successfully!", "success")
            return redirect(url_for('list_transportation'))
        except Exception as e:
            flash(f"Error creating shipment: {str(e)}", "danger")

    return render_template('add_transportation.html', vehicles=vehicles, crops=crops)


@app.route('/transportation/edit/<int:transport_id>', methods=['GET', 'POST'])
def edit_transportation(transport_id):
    """Update shipment status and details."""
    trans = safe_query("SELECT * FROM Transportation WHERE transport_id = %s;", (transport_id,), fetchone=True)
    if not trans:
        flash("Shipment not found.", "danger")
        return redirect(url_for('list_transportation'))

    vehicles = safe_query("SELECT vehicle_id, vehicle_number, driver_name, vehicle_type FROM Vehicle ORDER BY vehicle_number ASC;", fetchall=True)
    crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)

    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id')
        crop_id = request.form.get('crop_id')
        source = request.form.get('source', '').strip()
        destination = request.form.get('destination', '').strip()
        quantity = float(request.form.get('quantity', trans['quantity']))
        transport_date = request.form.get('transport_date', trans['transport_date'])
        status = request.form.get('status', trans['status'])

        try:
            safe_query("""
                UPDATE Transportation
                SET vehicle_id = %s, crop_id = %s, source = %s, destination = %s,
                    quantity = %s, transport_date = %s, status = %s
                WHERE transport_id = %s;
            """, (vehicle_id, crop_id, source, destination, quantity, transport_date, status, transport_id), commit=True)
            flash("Shipment status updated!", "success")
            return redirect(url_for('list_transportation'))
        except Exception as e:
            flash(f"Error updating shipment: {str(e)}", "danger")

    return render_template('edit_transportation.html', trans=trans, vehicles=vehicles, crops=crops)


@app.route('/transportation/delete/<int:transport_id>', methods=['POST'])
def delete_transportation(transport_id):
    """Delete a transport shipment."""
    try:
        safe_query("DELETE FROM Transportation WHERE transport_id = %s;", (transport_id,), commit=True)
        flash("Shipment record deleted.", "success")
    except Exception as e:
        flash(f"Error deleting shipment: {str(e)}", "danger")
    return redirect(url_for('list_transportation'))


# =============================================================================
# 11. Customer & Retail Sales Routes
# =============================================================================

@app.route('/customers')
def list_customers():
    """View registered customers."""
    customers = safe_query("SELECT * FROM Customer ORDER BY customer_id ASC;", fetchall=True)
    return render_template('customers.html', customers=customers)


@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    """Add a new customer."""
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        try:
            safe_query("""
                INSERT INTO Customer (customer_name, phone, address)
                VALUES (%s, %s, %s);
            """, (customer_name, phone, address), commit=True)
            flash(f"Customer '{customer_name}' registered!", "success")
            return redirect(url_for('list_customers'))
        except Exception as e:
            flash(f"Error adding customer: {str(e)}", "danger")

    return render_template('add_customer.html')


@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    """Edit customer profile."""
    customer = safe_query("SELECT * FROM Customer WHERE customer_id = %s;", (customer_id,), fetchone=True)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for('list_customers'))

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        try:
            safe_query("""
                UPDATE Customer
                SET customer_name = %s, phone = %s, address = %s
                WHERE customer_id = %s;
            """, (customer_name, phone, address, customer_id), commit=True)
            flash(f"Customer '{customer_name}' updated!", "success")
            return redirect(url_for('list_customers'))
        except Exception as e:
            flash(f"Error updating customer: {str(e)}", "danger")

    return render_template('edit_customer.html', customer=customer)


@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    """Delete a customer."""
    try:
        safe_query("DELETE FROM Customer WHERE customer_id = %s;", (customer_id,), commit=True)
        flash("Customer deleted.", "success")
    except Exception as e:
        flash(f"Error deleting customer: {str(e)}", "danger")
    return redirect(url_for('list_customers'))


@app.route('/sales')
def list_sales():
    """View retail sales log."""
    query = """
        SELECT s.sale_id, cu.customer_name, r.retailer_name,
               c.crop_name, c.unit, s.quantity, s.price_per_unit, s.total_price, s.sale_date
        FROM Sales s
        JOIN Customer cu ON s.customer_id = cu.customer_id
        JOIN Retailer r ON s.retailer_id = r.retailer_id
        JOIN Crop c ON s.crop_id = c.crop_id
    """
    params = ()
    if session.get('role') == 'retailer':
        query += " WHERE s.retailer_id = %s"
        params = (session['entity_id'],)
    elif session.get('role') == 'customer':
        query += " WHERE s.customer_id = %s"
        params = (session['entity_id'],)
    query += " ORDER BY s.sale_date DESC, s.sale_id DESC;"
    sales = safe_query(query, params, fetchall=True)
    return render_template('sales.html', sales=sales)


@app.route('/sales/add', methods=['GET', 'POST'])
def add_sale():
    """Record consumer retail sale."""
    if session.get('role') == 'retailer':
        customers = []
    else:
        customers = safe_query("SELECT customer_id, customer_name, phone FROM Customer ORDER BY customer_name ASC;", fetchall=True)
    if session.get('role') == 'retailer':
        retailers = safe_query(
            "SELECT retailer_id, retailer_name, address FROM Retailer WHERE retailer_id = %s;",
            (session['entity_id'],),
            fetchall=True
        )
    else:
        retailers = safe_query("SELECT retailer_id, retailer_name, address FROM Retailer ORDER BY retailer_name ASC;", fetchall=True)
    if session.get('role') == 'retailer':
        crops = safe_query("""
            SELECT c.crop_id, c.crop_name, c.unit
            FROM Crop c
            JOIN Retail_Supply rs ON rs.crop_id = c.crop_id
            LEFT JOIN (
                SELECT crop_id, SUM(quantity) AS quantity_sold
                FROM Sales
                WHERE retailer_id = %s
                GROUP BY crop_id
            ) s ON s.crop_id = c.crop_id
            WHERE rs.retailer_id = %s
            GROUP BY c.crop_id, c.crop_name, c.unit, s.quantity_sold
            HAVING SUM(rs.quantity) - COALESCE(s.quantity_sold, 0) > 0
            ORDER BY c.crop_name;
        """, (session['entity_id'], session['entity_id']), fetchall=True)
    else:
        crops = safe_query("SELECT crop_id, crop_name, unit FROM Crop ORDER BY crop_name ASC;", fetchall=True)

    if request.method == 'POST':
        retailer_id = session['entity_id'] if session.get('role') == 'retailer' else request.form.get('retailer_id')
        crop_id = request.form.get('crop_id')
        try:
            quantity = float(request.form.get('quantity', 0))
            price_per_unit = float(request.form.get('price_per_unit', 0))
        except (TypeError, ValueError):
            quantity = 0
            price_per_unit = -1
        sale_date = request.form.get('sale_date', date.today().isoformat())
        total_price = quantity * price_per_unit

        if quantity <= 0 or price_per_unit < 0:
            flash("Quantity must be positive and price must be non-negative.", "danger")
            return render_template('add_sale.html', customers=customers, retailers=retailers, crops=crops)

        if session.get('role') == 'retailer':
            customer_name = request.form.get('customer_name', '').strip()
            customer_phone = request.form.get('customer_phone', '').strip()
            customer_address = request.form.get('customer_address', '').strip()
            if not customer_name or not customer_phone or not customer_address:
                flash("Enter the customer name, phone, and address.", "danger")
                return render_template('add_sale.html', customers=customers, retailers=retailers, crops=crops)
            crop_exists = safe_query(
                "SELECT crop_id FROM Crop WHERE crop_id = %s;",
                (crop_id,),
                fetchone=True
            )
            stock = safe_query("""
                SELECT COALESCE(SUM(rs.quantity), 0) - COALESCE(MAX(s.quantity_sold), 0) AS available
                FROM Retail_Supply rs
                LEFT JOIN (
                    SELECT retailer_id, crop_id, SUM(quantity) AS quantity_sold
                    FROM Sales
                    WHERE retailer_id = %s AND crop_id = %s
                    GROUP BY retailer_id, crop_id
                ) s ON s.retailer_id = rs.retailer_id AND s.crop_id = rs.crop_id
                WHERE rs.retailer_id = %s AND rs.crop_id = %s;
            """, (retailer_id, crop_id, retailer_id, crop_id), fetchone=True)
            if not crop_exists or not stock or stock['available'] < quantity:
                flash("Sale quantity exceeds your available stock.", "danger")
                return render_template('add_sale.html', customers=customers, retailers=retailers, crops=crops)
            customer = safe_query(
                "SELECT customer_id FROM Customer WHERE phone = %s;",
                (customer_phone,),
                fetchone=True
            )
            customer_id = customer['customer_id'] if customer else safe_query(
                "INSERT INTO Customer (customer_name, phone, address) VALUES (%s, %s, %s);",
                (customer_name, customer_phone, customer_address),
                commit=True
            )
        else:
            customer_id = request.form.get('customer_id')

        try:
            safe_query("""
                INSERT INTO Sales (customer_id, retailer_id, crop_id, quantity, price_per_unit, total_price, sale_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (customer_id, retailer_id, crop_id, quantity, price_per_unit, total_price, sale_date), commit=True)
            flash("Retail sale transaction recorded successfully!", "success")
            return redirect(url_for('list_sales'))
        except Exception as e:
            flash(f"Error logging sale: {str(e)}", "danger")

    return render_template('add_sale.html', customers=customers, retailers=retailers, crops=crops)


@app.route('/sales/delete/<int:sale_id>', methods=['POST'])
def delete_sale(sale_id):
    """Delete a sales record."""
    try:
        safe_query("DELETE FROM Sales WHERE sale_id = %s;", (sale_id,), commit=True)
        flash("Sale record deleted.", "success")
    except Exception as e:
        flash(f"Error deleting sale: {str(e)}", "danger")
    return redirect(url_for('list_sales'))


@app.route('/customer/shop')
def customer_shop():
    """Display a storefront-style product grid for customers to browse available crops."""
    crops = get_retail_catalog()
    customer = safe_query(
        "SELECT customer_name, address FROM Customer WHERE customer_id = %s;",
        (session['entity_id'],),
        fetchone=True
    )
    return render_template('customer_shop.html', crops=crops, customer=customer)


@app.route('/customer/buy', methods=['POST'])
def customer_buy():
    """Creates a customer order from the storefront flow and schedules final-mile delivery."""
    address = request.form.get('address', '').strip()
    crop_id = request.form.get('crop_id')
    retailer_id = request.form.get('retailer_id')
    try:
        quantity = float(request.form.get('quantity', 0) or 0)
    except (TypeError, ValueError):
        quantity = 0

    if not address or not crop_id or not retailer_id:
        flash("Please provide a delivery address and select a produce item.", "danger")
        return redirect(url_for('customer_shop'))

    if quantity <= 0:
        flash("Quantity must be greater than zero.", "danger")
        return redirect(url_for('customer_shop'))

    crop = safe_query("SELECT crop_id, crop_name, unit FROM Crop WHERE crop_id = %s;", (crop_id,), fetchone=True)
    retailer = safe_query("SELECT retailer_id, retailer_name, address FROM Retailer WHERE retailer_id = %s;", (retailer_id,), fetchone=True)
    if not crop:
        flash("Selected crop could not be found.", "danger")
        return redirect(url_for('customer_shop'))
    if not retailer:
        flash("Selected retailer could not be found.", "danger")
        return redirect(url_for('customer_shop'))

    offer = safe_query("""
        SELECT rs.quantity - COALESCE(s.quantity_sold, 0) AS available_quantity,
               rs.price_per_unit
        FROM (
            SELECT retailer_id, crop_id, SUM(quantity) AS quantity,
                   MAX(price_per_unit) AS price_per_unit
            FROM Retail_Supply
            GROUP BY retailer_id, crop_id
        ) rs
        LEFT JOIN (
            SELECT retailer_id, crop_id, SUM(quantity) AS quantity_sold
            FROM Sales
            GROUP BY retailer_id, crop_id
        ) s ON s.retailer_id = rs.retailer_id AND s.crop_id = rs.crop_id
        WHERE rs.retailer_id = %s AND rs.crop_id = %s;
    """, (retailer_id, crop_id), fetchone=True)
    if not offer or offer['available_quantity'] < quantity:
        flash("The selected retailer does not have enough stock for this order.", "danger")
        return redirect(url_for('customer_shop'))

    customer = safe_query(
        "SELECT customer_id, address FROM Customer WHERE customer_id = %s;",
        (session['entity_id'],),
        fetchone=True
    )
    if not customer:
        session.clear()
        flash('Your customer profile is no longer available. Contact an administrator.', 'danger')
        return redirect(url_for('login'))

    customer_id = session['entity_id']
    if customer['address'] != address:
        safe_query(
            "UPDATE Customer SET address = %s WHERE customer_id = %s;",
            (address, customer_id),
            commit=True
        )

    price_per_unit = offer['price_per_unit']
    total_price = quantity * price_per_unit
    sale_date = date.today().isoformat()
    sale_id = safe_query(
        """
            INSERT INTO Sales (customer_id, retailer_id, crop_id, quantity, price_per_unit, total_price, sale_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """,
        (customer_id, retailer_id, crop_id, quantity, price_per_unit, total_price, sale_date),
        commit=True
    )

    vehicle = safe_query(
        "SELECT vehicle_id, vehicle_number, driver_name FROM Vehicle ORDER BY vehicle_id ASC LIMIT 1;",
        fetchone=True
    )
    if not vehicle:
        flash("Order placed, but no vehicle is currently available for delivery.", "warning")
        return redirect(url_for('customer_track', sale_id=sale_id))

    source = retailer['retailer_name']
    destination = address
    safe_query(
        """
            INSERT INTO Transportation (vehicle_id, crop_id, source, destination, quantity, transport_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'In Transit');
        """,
        (vehicle['vehicle_id'], crop_id, source, destination, quantity, sale_date),
        commit=True
    )

    flash(f"Order placed successfully! Your order ID is {sale_id}.", "success")
    return redirect(url_for('customer_track', sale_id=sale_id))


@app.route('/customer/track', methods=['GET', 'POST'])
def customer_track():
    """Search and display the status of a customer order through a storefront-style tracking page."""
    search_term = ''
    result = None

    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        sale_id = request.form.get('sale_id', '').strip()
    else:
        search_term = request.args.get('search_term', '').strip()
        sale_id = request.args.get('sale_id', '').strip()
    sale_id = sale_id or (search_term if search_term.isdigit() else '')

    if sale_id:
        result = safe_query("""
            SELECT s.sale_id,
                   s.sale_date,
                   s.quantity AS order_quantity,
                   s.price_per_unit,
                   s.total_price,
                   cu.customer_name,
                   cu.phone,
                   cu.address,
                   c.crop_name,
                   c.unit,
                   r.retailer_name,
                   COALESCE(MAX(t.transport_id), 0) AS transport_id,
                   MAX(t.status) AS delivery_status,
                   MAX(v.vehicle_number) AS vehicle_number,
                   MAX(v.driver_name) AS driver_name,
                   MAX(v.driver_phone) AS driver_phone,
                   MAX(t.destination) AS destination,
                   MAX(t.source) AS source
            FROM Sales s
            JOIN Customer cu ON s.customer_id = cu.customer_id
            JOIN Crop c ON s.crop_id = c.crop_id
            JOIN Retailer r ON s.retailer_id = r.retailer_id
            LEFT JOIN Transportation t
                ON t.crop_id = s.crop_id
               AND ABS(t.quantity - s.quantity) < 0.0001
               AND t.destination = cu.address
            LEFT JOIN Vehicle v ON t.vehicle_id = v.vehicle_id
            WHERE s.customer_id = %s AND s.sale_id = %s
            GROUP BY s.sale_id, s.sale_date, s.quantity, s.price_per_unit, s.total_price,
                     cu.customer_name, cu.phone, cu.address, c.crop_name, c.unit, r.retailer_name
            ORDER BY s.sale_id DESC
            LIMIT 1;
        """, (session['entity_id'], sale_id), fetchone=True)

    if result:
        result['status_label'] = get_tracking_status(result.get('delivery_status'))
        result['estimated_arrival'] = get_estimated_arrival(result.get('delivery_status'))
        result['timeline'] = [
            {'label': 'Ordered', 'done': True},
            {'label': 'Dispatched', 'done': result['status_label'] in ('In Transit', 'Out for Delivery', 'Delivered')},
            {'label': 'In Transit', 'done': result['status_label'] in ('Out for Delivery', 'Delivered')},
            {'label': 'Delivered', 'done': result['status_label'] == 'Delivered'}
        ]

    return render_template('customer_track.html', result=result, search_term=search_term, sale_id=sale_id)


# =============================================================================
# 12. DBMS Analytical Reports Route (11 SQL Reports)
# =============================================================================

@app.route('/reports')
@role_required('admin')
def reports():
    """Generates 11 comprehensive DBMS analytical reports."""
    is_connected, msg, _ = test_connection()
    if not is_connected:
        flash(f"Please configure MySQL before viewing reports: {msg}", "warning")
        return redirect(url_for('db_setup'))

    try:
        # Report 1: Farmer-wise crop supply
        report1 = safe_query("""
            SELECT f.farmer_id, f.name AS farmer_name, f.village, f.phone,
                   COUNT(cs.supply_id) AS total_supplies_count,
                   COALESCE(SUM(cs.quantity), 0) AS total_quantity_supplied,
                   COALESCE(SUM(cs.total_amount), 0) AS total_earnings
            FROM Farmer f
            LEFT JOIN Crop_Supply cs ON f.farmer_id = cs.farmer_id
            GROUP BY f.farmer_id, f.name, f.village, f.phone
            ORDER BY total_earnings DESC;
        """, fetchall=True)

        # Report 2: Crop-wise total production
        report2 = safe_query("""
            SELECT c.crop_name, c.crop_type, c.unit,
                   COUNT(p.production_id) AS records_count,
                   COALESCE(SUM(p.quantity), 0) AS total_produced,
                   COALESCE(ROUND(AVG(p.quantity), 2), 0) AS avg_production
            FROM Crop c
            LEFT JOIN Production p ON c.crop_id = p.crop_id
            GROUP BY c.crop_id, c.crop_name, c.crop_type, c.unit
            ORDER BY total_produced DESC;
        """, fetchall=True)

        # Report 3: Crop-wise available inventory
        report3 = safe_query("""
            SELECT c.crop_id, c.crop_name, c.crop_type, c.unit,
                   COALESCE(SUM(i.quantity), 0) AS total_stock,
                   COUNT(DISTINCT i.warehouse_id) AS warehouses_count
            FROM Crop c
            LEFT JOIN Inventory i ON c.crop_id = i.crop_id
            GROUP BY c.crop_id, c.crop_name, c.crop_type, c.unit
            ORDER BY total_stock DESC;
        """, fetchall=True)

        # Report 4: Warehouse-wise inventory & occupancy
        report4 = safe_query("""
            SELECT w.warehouse_name, w.location, w.capacity,
                   COALESCE(SUM(i.quantity), 0) AS total_occupied,
                   (w.capacity - COALESCE(SUM(i.quantity), 0)) AS available_space,
                   ROUND((COALESCE(SUM(i.quantity), 0) / w.capacity) * 100, 2) AS utilization_percent
            FROM Warehouse w
            LEFT JOIN Inventory i ON w.warehouse_id = i.warehouse_id
            GROUP BY w.warehouse_id, w.warehouse_name, w.location, w.capacity
            ORDER BY utilization_percent DESC;
        """, fetchall=True)

        # Report 5: Distributor purchases
        report5 = safe_query("""
            SELECT d.distributor_name, d.phone,
                   COUNT(p.purchase_id) AS orders_count,
                   COALESCE(SUM(p.quantity), 0) AS total_quantity,
                   COALESCE(SUM(p.total_price), 0) AS total_spent
            FROM Distributor d
            LEFT JOIN Purchase p ON d.distributor_id = p.distributor_id
            GROUP BY d.distributor_id, d.distributor_name, d.phone
            ORDER BY total_spent DESC;
        """, fetchall=True)

        # Report 6: Retailer supplies
        report6 = safe_query("""
            SELECT r.retailer_name, r.phone,
                   COUNT(rs.retail_supply_id) AS supplies_count,
                   COALESCE(SUM(rs.quantity), 0) AS total_quantity,
                   COALESCE(SUM(rs.total_price), 0) AS total_cost
            FROM Retailer r
            LEFT JOIN Retail_Supply rs ON r.retailer_id = rs.retailer_id
            GROUP BY r.retailer_id, r.retailer_name, r.phone
            ORDER BY total_cost DESC;
        """, fetchall=True)

        # Report 7: Transportation status
        report7 = safe_query("""
            SELECT status, COUNT(transport_id) AS trips_count,
                   COALESCE(SUM(quantity), 0) AS total_quantity
            FROM Transportation
            GROUP BY status
            ORDER BY trips_count DESC;
        """, fetchall=True)

        # Report 8: Customer sales
        report8 = safe_query("""
            SELECT cu.customer_name, cu.phone,
                   COUNT(s.sale_id) AS purchases_count,
                   COALESCE(SUM(s.quantity), 0) AS total_quantity,
                   COALESCE(SUM(s.total_price), 0) AS total_spent
            FROM Customer cu
            LEFT JOIN Sales s ON cu.customer_id = s.customer_id
            GROUP BY cu.customer_id, cu.customer_name, cu.phone
            ORDER BY total_spent DESC;
        """, fetchall=True)

        # Report 9: Total revenue breakdown
        report9 = {
            'farmer_supply_total': safe_query("SELECT COALESCE(SUM(total_amount), 0) AS total FROM Crop_Supply;", fetchone=True)['total'],
            'distributor_purchase_total': safe_query("SELECT COALESCE(SUM(total_price), 0) AS total FROM Purchase;", fetchone=True)['total'],
            'retail_supply_total': safe_query("SELECT COALESCE(SUM(total_price), 0) AS total FROM Retail_Supply;", fetchone=True)['total'],
            'retail_sales_total': safe_query("SELECT COALESCE(SUM(total_price), 0) AS total FROM Sales;", fetchone=True)['total']
        }

        # Report 10: Most supplied crop
        report10 = safe_query("""
            SELECT c.crop_name, c.crop_type, c.unit,
                   COUNT(cs.supply_id) AS supply_count,
                   COALESCE(SUM(cs.quantity), 0) AS total_quantity,
                   COALESCE(SUM(cs.total_amount), 0) AS total_value
            FROM Crop c
            JOIN Crop_Supply cs ON c.crop_id = cs.crop_id
            GROUP BY c.crop_id, c.crop_name, c.crop_type, c.unit
            ORDER BY total_quantity DESC;
        """, fetchall=True)

        # Report 11: Low-stock crops
        report11 = safe_query("""
            SELECT w.warehouse_name, c.crop_name, c.unit, i.quantity
            FROM Inventory i
            JOIN Warehouse w ON i.warehouse_id = w.warehouse_id
            JOIN Crop c ON i.crop_id = c.crop_id
            WHERE i.quantity < 300.00
            ORDER BY i.quantity ASC;
        """, fetchall=True)

        return render_template(
            'reports.html',
            report1=report1,
            report2=report2,
            report3=report3,
            report4=report4,
            report5=report5,
            report6=report6,
            report7=report7,
            report8=report8,
            report9=report9,
            report10=report10,
            report11=report11
        )
    except Exception as e:
        flash(f"Error compiling DBMS reports: {str(e)}", "danger")
        return redirect(url_for('db_setup'))


# =============================================================================
# Application Entry Point
# =============================================================================
if __name__ == '__main__':
    # Print startup message for college student
    print("=" * 70)
    print("🌾 Starting Crop Supply Chain Management System...")
    print("🌐 Open http://127.0.0.1:5000 in your web browser.")
    print("📌 Initialize database/schema.sql and database/sample_data.sql before signing in.")
    print("=" * 70)
    app.run(host='127.0.0.1', port=5000, debug=Config.DEBUG)
