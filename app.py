# Shamelessly copied from http://flask.pocoo.org/docs/quickstart/

# from flask import Flask
# app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     return 'Hello World!'

# if __name__ == '__main__':
#     app.run()

from flask import Flask, render_template, redirect, url_for, flash, request
import sqlite3
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, EmailField, IntegerField, FloatField, SelectField, FileField
from wtforms.validators import DataRequired, NumberRange
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import logging
import os
import matplotlib.pyplot as plt
from flask import session, render_template
import io
import base64

app = Flask(__name__)
# Replace with your own secret key
app.config['SECRET_KEY'] = 'your_secret_key'

# Set up basic logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # You can change this to INFO, WARNING, etc.
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Optionally, create a file handler for logging to a file
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(file_handler)

# Database helper functions


def get_db_connection():
    conn = sqlite3.connect('site.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute('''  
            CREATE TABLE IF NOT EXISTS user (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
        username TEXT NOT NULL UNIQUE,  
        password TEXT NOT NULL,  
        fullname TEXT NOT NULL,  
        description TEXT NOT NULL,  
        pincode TEXT NOT NULL,  
        servicename TEXT,
        experience INTEGER,
        file_upload TEXT,
        status TEXT,
        role TEXT NOT NULL  
    )  
''')

        conn.execute('''  
            CREATE TABLE IF NOT EXISTS service (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                name TEXT NOT NULL,  
                price REAL NOT NULL,  
                description TEXT
            )  
        ''')
        conn.execute('''  
            CREATE TABLE IF NOT EXISTS service_request (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER,
                customer_id INTEGER,
                professional_id INTEGER,
                date_of_request TEXT DEFAULT CURRENT_TIMESTAMP,
                date_of_completion TEXT,
                service_status TEXT DEFAULT 'requested',
                remarks TEXT,
                rating INTEGER,
                FOREIGN KEY (service_id) REFERENCES service(id),
                FOREIGN KEY (customer_id) REFERENCES user(id),
                FOREIGN KEY (professional_id) REFERENCES user(id)
            )  
        ''')


# Initialize the database
init_db()


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "admin":
            return redirect(url_for('admin_dashboard'))
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM user WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:   
            session['user_id'] = user['id'] 
            flash('Login successful.')
            if user['role'] == "professional":
                if user['status']=="accepted":
                    return redirect(url_for('professional_dashboard'))
                else:
                    flash('You are not approved yet, please check with admin! Thank you.')
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password')

    return render_template('login.html')

# Create a Registration Form


class CustomerSignUp(FlaskForm):
    username = EmailField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    fullname = StringField('Fullname')
    description = TextAreaField('Address')
    pincode = IntegerField('Pin code', validators=[
                           NumberRange(min=100000, max=999999)])
    submit = SubmitField('Register')


@app.route('/customersignup', methods=['GET', 'POST'])
def customersignup():
    form = CustomerSignUp()  # Instantiate the form object
    if form.validate_on_submit():  # If the form is valid on submission

        username = form.username.data
        password = form.password.data
        fullname = form.fullname.data
        description = form.description.data
        pincode = form.pincode.data

        # Hash the password before storing it
        # hashed_password = generate_password_hash(password)

        # Save the data to your database
        conn = get_db_connection()
        conn.execute('INSERT INTO user (username, password, fullname, description, pincode, role) VALUES (?, ?, ?, ?, ?, "customer")',
                     (username, password, fullname, description, pincode))
        conn.commit()
        conn.close()

        flash('Registration successful. Please log in.')

        # Redirect after successful registration
        return redirect(url_for('login'))
    # Pass the form to the template
    return render_template('customer/customersignup.html', form=form)


class ProfessionalSignUp(FlaskForm):
    username = EmailField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    fullname = StringField('Fullname')
    servicename = SelectField('Service Name',validators=[DataRequired()])
    fileUpload = FileField('Upload Signed PDF', validators=[DataRequired()])
    description = TextAreaField('Address')
    experience = IntegerField('Experience', validators=[
                              NumberRange(min=0, max=50)])
    pincode = IntegerField('Pin code', validators=[
                           NumberRange(min=100000, max=999999)])
    submit = SubmitField('Register')


@app.route('/professionalsignup', methods=['GET', 'POST'])
def professionalsignup():
    
    conn = get_db_connection()
    
    # Fetch services from the database
    services = conn.execute('SELECT id, name FROM service').fetchall()
    conn.close()

    # Prepare the choices for the SelectField
    service_choices = [(str(service['id']), service['name']) for service in services]
    
    form = ProfessionalSignUp()  # Instantiate the form object
    form.servicename.choices = service_choices
    app.logger.debug("ousite profe condition")
    if form.validate_on_submit():  # If the form is valid on submission
        app.logger.debug("inside profe condition")
        username = form.username.data
        password = form.password.data
        fullname = form.fullname.data
        description = form.description.data
        experience = form.experience.data
        pincode = form.pincode.data
        servicename = form.servicename.data  # Get the selected service
        file_upload = form.fileUpload.data  # Get the uploaded file
        app.logger.debug("gonna save file inside profe condition")
        app.logger.debug(f"Username: {username}")
        app.logger.debug(f"Password: {password}")
        app.logger.debug(f"Fullname: {fullname}")
        app.logger.debug(f"Description: {description}")
        app.logger.debug(f"Pincode: {pincode}")
        app.logger.debug(
            f"Servicename: {servicename} and type: {type(servicename)}")
        app.logger.debug(f"File upload: {file_upload}")
        # Save the file (optional: you can define a specific directory for file uploads)
        filename = None
        if file_upload:
            filename = secure_filename(file_upload.filename)
            os.makedirs('uploads', exist_ok=True)
            file_upload.save(os.path.join('uploads', filename))
            app.logger.debug("The path of file is: " +
                             os.path.join('uploads', filename))
            app.logger.debug(f"File name: {filename}")

        # Hash the password before storing it
        # hashed_password = generate_password_hash(password)
        app.logger.debug("to save in table")
        # Save the data to your database
        conn = get_db_connection()
        conn.execute('INSERT INTO user (username, password, fullname, description, pincode, servicename, file_upload, experience, role) VALUES (?, ?, ?, ?, ?, ?, ?, ?, "professional")',
                     (username, password, fullname, description, pincode, servicename, filename, experience))
        conn.commit()
        conn.close()
        app.logger.debug("saved in table")
        flash('Registration successful. Please log in.')

        # Redirect after successful registration
        return redirect(url_for('login'))
    # Pass the form to the template
    return render_template('professional/professionalsignup.html', form=form)


@app.route('/edit_professional/<int:id>', methods=['GET', 'POST'])
def edit_professional(id):
    conn = get_db_connection()
    
    # Fetch services from the database
    services = conn.execute('SELECT id, name FROM service').fetchall()
    conn.close()

    # Prepare the choices for the SelectField
    service_choices = [(str(service['id']), service['name']) for service in services]
    form = ProfessionalSignUp()  # Instantiate the form object
    form.servicename.choices = service_choices
    
    conn = get_db_connection()

    # Fetch the existing professional data
    professional = conn.execute(
        'SELECT * FROM user WHERE id = ?', (id,)).fetchone()
    conn.close()

    # If professional doesn't exist, redirect or show an error
    if not professional:
        flash('Professional not found!', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Pre-fill the form with existing professional data
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        fullname = form.fullname.data
        description = form.description.data
        experience = form.experience.data
        pincode = form.pincode.data
        servicename = form.servicename.data
        file_upload = form.fileUpload.data
        filename = None

        # Handle file upload
        if file_upload:
            filename = secure_filename(file_upload.filename)
            os.makedirs('uploads', exist_ok=True)
            file_upload.save(os.path.join('uploads', filename))

        # Update the professional data
        conn = get_db_connection()
        conn.execute('''
            UPDATE user SET username = ?, password = ?, fullname = ?, description = ?, pincode = ?, 
            servicename = ?, file_upload = ?, experience = ? WHERE id = ?
        ''', (username, password, fullname, description, pincode, servicename, filename, experience, id))
        conn.commit()
        conn.close()

        flash('Professional updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Fill the form with the current values
    form.username.data = professional['username']
    form.password.data = professional['password']
    form.fullname.data = professional['fullname']
    form.servicename.data = professional['servicename']
    form.description.data = professional['description']
    form.experience.data = professional['experience']
    form.pincode.data = professional['pincode']
    return render_template('professional/edit_professional.html', form=form, professional=professional)


@app.route('/delete_professional/<int:id>', methods=['GET'])
def delete_professional(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM user WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Professional deleted successfully!', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/professional/<int:id>', methods=['GET'])
def professional_details(id):
    conn = get_db_connection()
    professional = conn.execute(
        'SELECT * FROM user WHERE id = ? AND role = "professional"', (id,)).fetchone()
    conn.close()
    if professional is None:
        flash('Professional not found.')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/professional_details.html', professional=professional)


@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    conn = get_db_connection()
    services = conn.execute('SELECT * FROM service').fetchall()
    professionals = conn.execute(
        'SELECT * FROM user WHERE role = ?', ('professional',)).fetchall()
    # Fetch service requests and related data (e.g., service name, professional, and customer names)
    service_requests = conn.execute('''
        SELECT sr.id, s.name AS service_name, u.fullname AS professional_name, 
               u2.fullname AS customer_name, sr.service_status 
        FROM service_request sr
        JOIN service s ON sr.service_id = s.id
        JOIN user u ON sr.professional_id = u.id
        JOIN user u2 ON sr.customer_id = u2.id
    ''').fetchall()
    service_requests = conn.execute('SELECT * FROM service_request').fetchall()
    for professional in professionals:
        app.logger.debug(professional[3])
    conn.close()
    return render_template('admin/admin_dashboard.html', services=services, professionals=professionals, service_requests=service_requests)


@app.route('/accept_professional/<int:id>', methods=['GET', 'POST'])
def accept_professional(id):
    # Logic to accept a professional (e.g., updating their status in the database)
    conn = get_db_connection()
    conn.execute('UPDATE user SET status = "accepted" WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Professional has been accepted!', 'success')
    # Redirect back to the admin dashboard
    return redirect(url_for('admin_dashboard'))


@app.route('/reject_professional/<int:id>', methods=['GET', 'POST'])
def reject_professional(id):
    # Logic to reject a professional (e.g., updating their status in the database)
    conn = get_db_connection()
    conn.execute('UPDATE user SET status = "rejected" WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Professional has been rejected!', 'warning')
    # Redirect back to the admin dashboard
    return redirect(url_for('admin_dashboard'))

# Create a Registration Form


class NewService(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Service')


@app.route('/new_service', methods=['GET', 'POST'])
def new_service():
    form = NewService()  # Instantiate the form object
    app.logger.debug("outside the if codition")
    if form.validate_on_submit():  # If the form is valid on submission
        app.logger.debug("inside the if codition")
        name = form.name.data
        price = form.price.data
        description = form.description.data

        # Save the data to your database
        conn = get_db_connection()
        conn.execute('INSERT INTO service (name, price, description) VALUES (?, ?, ?)',
                     (name, price, description))
        conn.commit()
        conn.close()
        flash('Created service successfully.')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/new_service.html', form=form)


@app.route('/delete_service/<int:id>', methods=['GET'])
def delete_service(id):
    # Connect to the database
    conn = get_db_connection()
    try:
        # Execute DELETE query using the service ID
        conn.execute('DELETE FROM service WHERE id = ?', (id,))
        conn.commit()
        flash('Service deleted successfully.')
    except Exception as e:
        app.logger.error(f"Error deleting service: {e}")
        flash('Error deleting service.')
    finally:
        conn.close()

    # Redirect back to the admin dashboard
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_service/<int:id>', methods=['GET', 'POST'])
def edit_service(id):
    # Retrieve the service to edit
    conn = get_db_connection()
    service = conn.execute(
        'SELECT * FROM service WHERE id = ?', (id,)).fetchone()
    conn.close()

    # If service doesn't exist, redirect with error message
    if service is None:
        flash('Service not found.')
        return redirect(url_for('admin_dashboard'))

    # Instantiate the form and pre-fill it with existing data
    form = NewService()
    if request.method == 'GET':
        form.name.data = service['name']
        form.price.data = service['price']
        form.description.data = service['description']

    if form.validate_on_submit():
        # If the form is valid, update the service
        name = form.name.data
        price = form.price.data
        description = form.description.data

        conn = get_db_connection()
        try:
            # Update the service data in the database
            conn.execute('''
                UPDATE service SET name = ?, price = ?, description = ? WHERE id = ?
            ''', (name, price, description, id))
            conn.commit()
            flash('Service updated successfully.')
        except Exception as e:
            app.logger.error(f"Error updating service: {e}")
            flash('Error updating service.')
        finally:
            conn.close()

        return redirect(url_for('admin_dashboard'))

    # Render the form template
    return render_template('admin/edit_service.html', form=form, service=service)


@app.route('/request_service', methods=['GET', 'POST'])
def request_service():
    # Logic for service request will go here
    return render_template('service_request.html')


@app.route('/admin/service/<int:id>', methods=['GET'])
def service_details(id):
    conn = get_db_connection()
    service = conn.execute(
        'SELECT * FROM service WHERE id = ?', (id,)).fetchone()
    conn.close()
    if service is None:
        flash('Service not found.')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/service_details.html', service=service)


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_results = None
    search_category = None
    if request.method == 'POST':
        search_category = request.form['search_category']
        search_query = request.form['search_query']

        conn = get_db_connection()

        if search_category == 'service':
            search_results = conn.execute(
                'SELECT * FROM service WHERE name LIKE ?', ('%' + search_query + '%',)).fetchall()

        elif search_category == 'professional':
            search_results = conn.execute(
                'SELECT * FROM user WHERE role = "professional" AND fullname LIKE ?', ('%' + search_query + '%',)).fetchall()

        conn.close()

    return render_template('admin/search.html', search_results=search_results, search_category=search_category)


@app.route('/summary')
def summary():
    conn = get_db_connection()

    # Fetch counts
    service_count = conn.execute('SELECT COUNT(*) FROM service').fetchone()[0]
    professional_count = conn.execute(
        'SELECT COUNT(*) FROM user WHERE role = "professional"').fetchone()[0]

    # Generate a simple plot (example: bar plot of service and professional counts)
    labels = ['Services', 'Professionals']
    counts = [service_count, professional_count]

    plt.bar(labels, counts)
    plt.title('Service and Professional Distribution')
    plt.xlabel('Category')
    plt.ylabel('Count')

    # Save the plot as an image
    os.makedirs('static/images', exist_ok=True)
    plt.savefig('static/images/service_plot.png')
    plt.close()

    conn.close()

    return render_template('admin/summary.html', service_count=service_count, professional_count=professional_count)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/professional/dashboard', methods=['GET'])
def professional_dashboard():
    user_id = session.get('user_id')  # Get logged-in user's ID
    app.logger.debug("The user id of the professional is: "+str(user_id))
    conn = get_db_connection()

    # Get all service requests with status 'requested' for this professional
    requested_services = conn.execute('''
        SELECT sr.*, s.name as service_name, c.fullname as customer_name
        FROM service_request sr
        JOIN service s ON sr.service_id = s.id
        JOIN user c ON sr.customer_id = c.id
        WHERE c.role='customer'  AND sr.service_status = 'requested'
    ''').fetchall()

    # Get accepted service requests (for historical purposes)
    accepted_services = conn.execute('''
        SELECT sr.*, s.name as service_name, c.fullname as customer_name
        FROM service_request sr
        JOIN service s ON sr.service_id = s.id
        JOIN user c ON sr.customer_id = c.id
        WHERE sr.professional_id = ? AND sr.service_status = 'accepted'
    ''', (user_id,)).fetchall()

    # Get rejected service requests
    rejected_services = conn.execute('''
        SELECT sr.*, s.name as service_name, c.fullname as customer_name
        FROM service_request sr
        JOIN service s ON sr.service_id = s.id
        JOIN user c ON sr.customer_id = c.id
        WHERE sr.professional_id = ? AND sr.service_status = 'rejected'
    ''', (user_id,)).fetchall()

    # Get closed service requests (closed is only available for accepted services)
    closed_services = conn.execute('''
        SELECT sr.*, s.name as service_name, c.fullname as customer_name
        FROM service_request sr
        JOIN service s ON sr.service_id = s.id
        JOIN user c ON sr.customer_id = c.id
        WHERE sr.professional_id = ? AND sr.service_status = 'closed'
    ''', (user_id,)).fetchall()

    conn.close()

    # Render home content
    return render_template('professional/professional_dashboard.html',
                           requested_services=requested_services,
                           accepted_services=accepted_services,
                           rejected_services=rejected_services,
                           closed_services=closed_services)


@app.route('/accept_service/<int:id>', methods=['POST'])
def accept_service(id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute(
        'UPDATE service_request SET service_status = "accepted", professional_id = ? WHERE id = ?',
        (user_id, id))
    conn.commit()
    conn.close()
    flash('Service has been accepted!', 'success')
    return redirect(url_for('professional_dashboard'))


@app.route('/reject_service/<int:id>', methods=['POST'])
def reject_service(id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE service_request SET service_status = "rejected", professional_id = ? WHERE id = ?',
        (user_id, id))
    conn.commit()
    conn.close()
    flash('Service has been rejected!', 'danger')
    return redirect(url_for('professional_dashboard'))


@app.route('/close_service/<int:id>', methods=['POST'])
def close_service(id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE service_request SET service_status = "closed" , customer_id = ? WHERE id = ?',
        (user_id, id))
    conn.commit()
    conn.close()
    flash('Service has been closed!', 'success')
    return redirect(url_for('professional_dashboard'))


@app.route('/professional/search', methods=['GET', 'POST'])
def search_service():
    user_id = session.get('user_id')
    columns = ['service_name', 'customer_name', 'service_status',
               'date_of_request']  # Example columns to search

    query = ''
    if request.method == 'POST':
        search_column = request.form['column']
        search_text = request.form['search_text']
        query = f"SELECT sr.*, s.name as service_name, c.fullname as customer_name FROM service_request sr JOIN service s ON sr.service_id = s.id JOIN user c ON sr.customer_id = c.id WHERE sr.professional_id = ? AND {search_column} LIKE ?"
        conn = get_db_connection()
        results = conn.execute(query, (user_id, f'%{search_text}%')).fetchall()
        conn.close()
        return render_template('professional/professional_dashboard.html', results=results)

    return render_template('professional/search_service.html', columns=columns)


@app.route('/professional/summary', methods=['GET'])
def summary_stats():
    user_id = session.get('user_id')
    conn = get_db_connection()

    # Fetch counts for each status type
    requested_count = conn.execute(
        'SELECT COUNT(*) FROM service_request WHERE professional_id = ? AND service_status = "requested"', (user_id,)).fetchone()[0]
    accepted_count = conn.execute(
        'SELECT COUNT(*) FROM service_request WHERE professional_id = ? AND service_status = "accepted"', (user_id,)).fetchone()[0]
    rejected_count = conn.execute(
        'SELECT COUNT(*) FROM service_request WHERE professional_id = ? AND service_status = "rejected"', (user_id,)).fetchone()[0]
    closed_count = conn.execute(
        'SELECT COUNT(*) FROM service_request WHERE professional_id = ? AND service_status = "closed"', (user_id,)).fetchone()[0]

    conn.close()

    # Create a bar chart with Matplotlib
    fig, ax = plt.subplots()
    statuses = ['Requested', 'Accepted', 'Rejected', 'Closed']
    counts = [requested_count, accepted_count, rejected_count, closed_count]

    ax.bar(statuses, counts, color=[
           '#FF5733', '#28A745', '#FFC107', '#007BFF'])
    ax.set_ylabel('Number of Requests')
    ax.set_title('Service Request Status Summary')

    # Save the plot to a BytesIO object and encode it as base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close(fig)  # Close the plot to free up memory

    # Return the rendered template with the image
    return render_template('professional/summary_stats.html', img_base64=img_base64)


class ServiceRemarkForm(FlaskForm):
    service_id = SelectField('Service ID', choices=[],
                             validators=[DataRequired()])
    remarks = StringField('Remarks', validators=[DataRequired()])
    rating = StringField('Rating (1-5)', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/customer', methods=['GET'])
def customer_dashboard():
    conn = get_db_connection()

    # Fetch available services
    services = conn.execute('SELECT * FROM service').fetchall()

    # Fetch service history for the logged-in customer (assuming user_id is available)
    user_id = session.get('user_id')
    app.logger.debug("The user id of customer is: "+str(user_id))
    service_history = conn.execute('''SELECT sr.id, s.name AS service_name, u.fullname AS professional_name, sr.service_status 
                                      FROM service_request sr
                                      JOIN service s ON sr.service_id = s.id
                                      LEFT JOIN user u ON sr.professional_id = u.id
                                      WHERE sr.customer_id = ?''', (user_id,)).fetchall()
    conn.close()
    return render_template('customer/dashboard.html', services=services, service_history=service_history, form=ServiceRemarkForm())


@app.route('/book_service', methods=['POST'])
def book_service():
    service_id = request.form['service_id']
    user_id = session.get('user_id')  # Get logged-in user's ID
    # Insert into service_request table
    conn = get_db_connection()
    conn.execute('''INSERT INTO service_request (service_id, customer_id, service_status) 
                    VALUES (?, ?, ?)''', (service_id, user_id, 'requested'))  # Status is 'requested' initially
    conn.commit()
    conn.close()

    # Redirect back to the customer dashboard
    return redirect(url_for('customer_dashboard'))


# @app.route('/customer/dashboard')
# def dashboard():
#     form = ServiceRemarkForm()  # Create an instance of the form
#     with get_db_connection() as conn:
#         services = conn.execute('SELECT * FROM service').fetchall()
#         service_history = conn.execute(
#             'SELECT * FROM service_request WHERE customer_id = ?', (session.get('user_id'),)).fetchall()
#     return render_template('customer/dashboard.html', services=services, service_history=service_history, form=form)


@app.route('/customer/search', methods=['GET', 'POST'])
def customer_search():
    search_results = None
    search_category = None

    if request.method == 'POST':
        search_category = request.form['column_name']  # selected column
        search_query = request.form['search_text']  # search query

        conn = get_db_connection()

        # Search within the selected column
        if search_category == 'name':
            search_results = conn.execute(
                'SELECT * FROM service WHERE name LIKE ?', ('%' + search_query + '%',)).fetchall()
        elif search_category == 'price':
            search_results = conn.execute(
                'SELECT * FROM service WHERE price LIKE ?', ('%' + search_query + '%',)).fetchall()
        elif search_category == 'description':
            search_results = conn.execute(
                'SELECT * FROM service WHERE description LIKE ?', ('%' + search_query + '%',)).fetchall()

        conn.close()

    return render_template('customer/customer_search.html', search_results=search_results, search_category=search_category)


@app.route('/customer/submit-remark', methods=['POST'])
def submit_remark():
    form = ServiceRemarkForm()
    if form.validate_on_submit():
        with get_db_connection() as conn:
            conn.execute('INSERT INTO service_request (service_id, customer_id, remarks, service_status) VALUES (?, ?, ?, ?)',
                         (form.service_id.data, 1, form.remarks.data, 'closed'))  # Replace 1 with the actual customer ID
        flash('Remarks submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    flash('There was an issue with your submission.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/customer/summary', methods=['GET'])
def customer_summary():
    conn = get_db_connection()

    # Query the number of services and service requests
    num_services = conn.execute('SELECT COUNT(*) FROM service').fetchone()[0]
    num_requests = conn.execute(
        'SELECT COUNT(*) FROM service_request').fetchone()[0]

    # Create the plot
    fig, ax = plt.subplots()
    ax.bar(['Services', 'Service Requests'], [
           num_services, num_requests], color=['blue', 'green'])

    ax.set_title('Services vs Service Requests')
    ax.set_xlabel('Category')
    ax.set_ylabel('Count')

    # Save the plot to a BytesIO object and encode it as base64
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    # Close the connection
    conn.close()

    # Render the HTML template and pass the base64-encoded image
    return render_template('customer/customer_summary.html', plot_url=plot_url)

@app.route('/close_service_request/<int:service_request_id>', methods=['POST'])
def close_service_request(service_request_id):
    remarks = request.form['remarks']
    rating = request.form['rating']

    # Assuming user is logged in and you have user_id available
    user_id = session.get('user_id')  # Get logged-in user's ID

    # Update the service request in the database with remarks and rating
    conn = get_db_connection()
    conn.execute('''UPDATE service_request 
                    SET service_status = 'closed', remarks = ?, rating = ? 
                    WHERE id = ? AND customer_id = ?''', 
                    (remarks, rating, service_request_id, user_id))
    app.logger.debug("values setted to it 11")
    conn.commit()
    conn.close()
    
    # conn = get_db_connection()
    # conn.execute(
    #     '''UPDATE service_request SET service_status = 'closed' , customer_id = ? WHERE id = ?''',
    #     (user_id, id))
    # conn.commit()
    # conn.close()

    # conn = get_db_connection()
    # status = conn.execute(
    #         '''SELECT service_status, remarks, rating FROM service_request WHERE id = ? AND customer_id = ? ''', 
    #                 (service_request_id, user_id)).fetchone()
    # conn.close()
    # app.logger.debug('the status is: '+str(status[0])+str(status[1])+str(status[2]))
    
    # Redirect the user to the customer dashboard or service history page
    return redirect(url_for('customer_dashboard'))  # Or another appropriate route


if __name__ == "__main__":
    app.run(debug=True)
