from flask import Flask, render_template, request, session, redirect, url_for, flash 
import pyodbc as odbc
import os



app = Flask(__name__)
app.secret_key = 'YOUR_SECURITY_KEY'

# #Connecting to DB

conn = odbc.connect(
    r'DRIVER={SQL Server};'
    r'SERVER=(YOUR_HOST_NAME);'
    r'DATABASE=ChaiWaye;'
    r'Trusted_Connection=yes;'
)

cursor = conn.cursor()



#VIEWS
from flask import render_template

@app.route("/")
def landing_page():
    # Fetch items
    cursor.execute('SELECT iid, iname, iprice, img, icategory FROM items')
    items = cursor.fetchall()

    item_column_names = [column[0] for column in cursor.description]

    grouped_items = {}
    for item in items:
        item_dict = dict(zip(item_column_names, item))
        category = item_dict['icategory']
        
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item_dict)

    # Fetch reviews
    cursor.execute('SELECT comment FROM reviews')
    reviews = cursor.fetchall()
    return render_template('LandingPage.html', grouped_items=grouped_items, reviews=reviews)




@app.route("/home" , methods=['GET', 'POST'])
def home():
    cursor.execute('SELECT iname, iprice, img, icategory FROM items')
    items = cursor.fetchall()

    grouped_items = {}
    column_names = [column[0] for column in cursor.description]

    for item in items:
        item_dict = dict(zip(column_names, item))
        category = item_dict['icategory']
        
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item_dict)

    return render_template('UserHome.html', grouped_items=grouped_items)


@app.route("/login" , methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM Customer WHERE username = ? AND cpassword = ?', (username, password))
        customer = cursor.fetchone()
        cursor.execute('SELECT iname, iprice, img, icategory FROM items')
        items = cursor.fetchall()

        grouped_items = {}
        column_names = [column[0] for column in cursor.description]

        for item in items:
            item_dict = dict(zip(column_names, item))
            category = item_dict['icategory']
        
            if category not in grouped_items:
                grouped_items[category] = []
        grouped_items[category].append(item_dict)
        if customer:
            session['username'] = customer[3]
            # session['cust_username'] = customer['username']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
            return render_template('UserHome.html', grouped_items=grouped_items) 
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
            return render_template('LandingPage.html',grouped_items=grouped_items)


@app.route("/profile" )
def Profile():
    return render_template('UserProfile.html')

@app.route("/AccountSettings",  methods=['GET', 'POST'])
def UserInfo():
    username = session.get('username')  
    cursor.execute('SELECT username, fname, lname, email, cmobile, caddress FROM customer WHERE CAST(username AS varchar(max)) = CAST(? AS varchar(max))', (username,))

    # cursor.execute('SELECT fname, lname, username, email, cmobile, caddress FROM customer WHERE CAST(username AS varchar(max)) = ?', (username,))

    custumer = cursor.fetchall()
    return render_template('UserInfo.html' , custumer=custumer)


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('landing_page'))

@app.route("/signup" , methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        fname = request.form['FirstName']
        lname = request.form['LastName']
        email = request.form['Email']
        password = request.form['password']
        phone_no = request.form['cmobile']
        address = request.form['address']

        cursor.execute("SELECT * FROM Customer WHERE email=?", (email,))
        existing_customer = cursor.fetchone()
        cursor.execute('SELECT iname, iprice, img, icategory FROM items')
        items = cursor.fetchall()

        grouped_items = {}
        column_names = [column[0] for column in cursor.description]

        for item in items:
            item_dict = dict(zip(column_names, item))
            category = item_dict['icategory']
        
            if category not in grouped_items:
                grouped_items[category] = []
        grouped_items[category].append(item_dict)
        if existing_customer:
            error_message = "Account already exists. Login to Continue!"
            return render_template('LandingPage.html', error_message=error_message,grouped_items=grouped_items)

        cursor.execute("INSERT INTO Customer (fname, lname, username, email, cmobile, caddress, cpassword) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (fname, lname, username, email, phone_no, address, password))
        conn.commit()

        # success_message = "Account successfully created! You can now log in."
        return redirect(url_for('home'))
        # return render_template('LandingPage.html', success_message=success_message)



    
@app.route('/admin', methods=['GET', 'POST'])
def AdminLogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute('SELECT * FROM admin WHERE aemail = ? AND apassword = ?', (email, password))
        admin = cursor.fetchone()

        if admin:
            session['admin_email'] = admin[0]
            flash('Login successful!', 'success')

            cursor.execute('SELECT iname, iprice, img, icategory FROM items')
            items = cursor.fetchall()

            grouped_items = {}

            for item in items:
                item_dict = dict(zip([column[0] for column in cursor.description], item))
                category = item_dict['icategory']
                
                if category not in grouped_items:
                    grouped_items[category] = []
                grouped_items[category].append(item_dict)

            return render_template('AdminDashboard.html', grouped_items=grouped_items)
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')

    return render_template('AdminLogin.html')

@app.route('/Dashboard', methods=['GET', 'POST'])
def AdminDashboard():
    cursor.execute('SELECT iname, iprice, img, icategory FROM items')
    items = cursor.fetchall()

    grouped_items = {}
    column_names = [column[0] for column in cursor.description]

    for item in items:
        item_dict = dict(zip(column_names, item))
        category = item_dict['icategory']
        
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item_dict)
    return render_template('AdminDashboard.html' , grouped_items=grouped_items)

@app.route('/PreviousOrders', methods=['GET', 'POST'])
def PreviousOrders():
    username = session.get('username')  

    if username:
        cursor.execute("""
            SELECT customer.*, orders.oid, items.iname, orders.ostatus
            FROM customer
            JOIN orders ON customer.cid = orders.cid
            JOIN items ON orders.iid = items.iid
            WHERE customer.username = ? AND orders.ostatus = 'Confirmed'
        """, (username,))
        
        corders = cursor.fetchall()
        return render_template('PreviousOrders.html', corders=corders)
    else:
        flash('You need to log in to view your previous orders.', 'warning')
        return redirect(url_for('login'))

@app.route('/PendingOrders', methods=['GET','POST'])
def PendingOrders():
    cursor.execute("""
        SELECT customer.*, orders.oid, items.iname, orders.ostatus
        FROM customer
        JOIN orders ON customer.cid = orders.cid
        JOIN items ON orders.iid = items.iid
        WHERE orders.ostatus = 'Pending'
    """)
    pendingorders=cursor.fetchall()
    return render_template('PendingOrders.html',pendingorders=pendingorders)

@app.route('/confirmation/<int:oid>', methods=['GET', 'POST'])
def confirmation(oid):
    cursor.execute('UPDATE orders SET ostatus = \'Confirmed\' WHERE oid = ?', oid)
    # conn.commit()  # Make sure to commit the changes to the database
    return redirect(url_for('PendingOrders'))

@app.route('/ConfirmedOrders', methods=['GET','POST'])
def ConfirmedOrders():
    cursor.execute("""
        SELECT customer.*, orders.oid, items.iname, orders.ostatus
        FROM customer
        JOIN orders ON customer.cid = orders.cid
        JOIN items ON orders.iid = items.iid
        WHERE orders.ostatus = 'Confirmed'
    """)
    confirmedorders=cursor.fetchall()
    return render_template('OrderHistory.html',confirmedorders=confirmedorders)

@app.route('/items')
def DisplayItems():
    cursor.execute('SELECT iid, iname, iprice,img FROM items')
    items = cursor.fetchall()
    return render_template('AdminDashboard.html',items=items)



image_upload_folder = 'static/img'
if not os.path.exists(image_upload_folder):
    os.makedirs(image_upload_folder)

@app.route('/addNewItem', methods=['GET', 'POST'])
def add_new_item():
    if request.method == 'POST':
        # Extract data from the form
        item_name = request.form['item_name']
        item_price = request.form['item_price']
        item_category = request.form['item_category'] 

        # Handle file upload
        if 'item_image' in request.files:
            image_file = request.files['item_image']
            if image_file.filename != '':
                # Use os.path.join to concatenate directory names
                image_path = os.path.abspath(os.path.join('static', 'img', image_file.filename))
                image_file.save(image_path)

                # Insert data into the 'items' table
                cursor.execute("INSERT INTO items (iname, iprice, img,icategory) VALUES (?, ?, ?,?)",
                               (item_name, item_price, image_file.filename, item_category))
                flash('Item added successfully!', 'success')
                conn.commit()

                # Fetch items and group them by category
                cursor.execute('SELECT iname, iprice, img, icategory FROM items')
                items = cursor.fetchall()

                grouped_items = {}

                # Iterate through items and group them by category
                for item in items:
                    item_dict = dict(zip([column[0] for column in cursor.description], item))
                    category = item_dict['icategory']
                    
                    if category not in grouped_items:
                        grouped_items[category] = []
                    grouped_items[category].append(item_dict)

                return render_template('AdminDashboard.html', grouped_items=grouped_items)

        flash('No file selected for upload', 'danger')

    return render_template('AddItem.html')

@app.route('/deleteItem/<string:item_name>', methods=['POST'])
def delete_item(item_name):
    cursor.execute("DELETE FROM items WHERE iname=?", (item_name,))
    conn.commit()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('AdminDashboard'))

cartItems = []
@app.route('/payment', methods=['POST'])
def index():
    return render_template('index.html')

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    try:
        
        customer_id = 1  

        # Iterate through the items in the cart and insert into the 'orders' table
        for item in cartItems:
            cursor.execute("INSERT INTO orders (cid, iid, ostatus) VALUES (?, ?, ?)",
                           (customer_id, item['iid'], 'Confirmed'))

        conn.commit()

        cartItems.clear()

        flash('Order confirmed successfully!', 'success')
        return redirect(url_for('index'))  

    except Exception as e:
        flash('Error confirming order. Please try again.', 'error')
        print(str(e))
        return redirect(url_for('index'))
    
@app.route("/Payment")
def payment():
    return render_template('Payment.html')

@app.route("/ProcessingOrder")
def processing_order():
    return render_template('ProcessingOrder.html')
# @app.route('/confirm_order', methods=['POST'])
# def confirm_order():
#     try:
#         data = request.get_json()
#         cart_items = data.get('cartItems', [])
#         total_bill = data.get('totalBill', 0)

#         # Insert the order details into the 'orders' table
#         for item in cart_items:ss
#             cursor.execute("INSERT INTO orders (cid, rid, iid, ostatus) VALUES (?, ?, ?, ?)",
#                            (customer_id, restaurant_id, item['itemId'], 'Confirmed'))
#             conn.commit()

#         # You can perform additional logic, such as updating the inventory or calculating order totals

#         return jsonify({'message': 'Order confirmed successfully'})

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/updateItem/<string:item_name>', methods=['GET', 'POST'])
# def update_item(item_name):
#     # Add code to handle updating an item
#     if request.method == 'POST':
#         # Extract updated data from the form
#         updated_name = request.form['updated_name']
#         updated_price = request.form['updated_price']
#         updated_category = request.form['updated_category']

#         # Update data in the 'items' table
#         cursor.execute("UPDATE items SET iname=?, iprice=?, icategory=? WHERE iname=?",
#                        (updated_name, updated_price, updated_category, item_name))
#         conn.commit()
#         flash('Item updated successfully!', 'success')
#         return redirect(url_for('AdminDashboard'))

#     # Fetch item details for pre-filling the update form
#     cursor.execute("SELECT iname, iprice, icategory FROM items WHERE iname=?", (item_name,))
#     item = cursor.fetchone()

    return render_template('UpdateItem.html', item=item)


app.run(debug=True)