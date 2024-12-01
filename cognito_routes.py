from flask import Blueprint, flash, redirect, request, jsonify, render_template, session, url_for
from app.cognito import CognitoManager, login_user, verify_token
from app.dynamo import get_products_from_dynamodb, get_user_order_history_from_dynamodb

auth_routes = Blueprint('auth', __name__)
cognito = CognitoManager()

@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        # Call the Cognito register_user function
        response = cognito.register_user(email, password)

        if response.get('success'):
            flash("Registration successful! Please verify your email.", "info")
            # Redirect to the verify page after registration
            return redirect(url_for('verify'))
        else:
            # Show an error message if registration fails
            flash(response.get('message', 'Registration failed. Please try again.'), "danger")
    
    # Render the registration page for GET requests
    return render_template('register.html')


@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        response = cognito.login_user(data['email'], data['password'])
        return jsonify(response)
    return render_template('login.html')

@auth_routes.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.form
        response = cognito.forgot_password(data['email'])
        return jsonify(response)
    return render_template('forgot_password.html')

@auth_routes.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        response = verify(email, code)
        if response['success']:
            flash(response['message'], 'success')
            return redirect(url_for('login'))
        else:
            flash(response['message'], 'danger')
    return render_template('verify.html')

main_routes = Blueprint('main_routes', __name__)

# Route to render the main page with products
@auth_routes.route('/')
def index():
    products = get_products_from_dynamodb()
    return render_template('index.html', products=products)

@auth_routes.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        # Call the Cognito login_user function to authenticate the user
        response = login_user(email, password)
        
        if isinstance(response, dict) and 'IdToken' in response:
            # Save the id_token in the session if login is successful
            session['id_token'] = response['IdToken']
            return redirect(url_for('auth.admin_page'))  # Redirect to the admin page
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('admin_login.html')

@auth_routes.route('/admin', methods=['GET'])
def admin_page():
    id_token = session.get('id_token')
    if not id_token:
        flash('You must be logged in to access the admin page.', 'warning')
        return redirect(url_for('auth.admin_login'))  # Redirect if token is missing

    # Verify the token to ensure the user is authenticated
    user = verify_token(id_token)
    if not user:
        flash('Invalid session or token. Please log in again.', 'danger')
        return redirect(url_for('auth.admin_login'))  # Redirect if token is invalid

    try:
        # Fetch the orders from DynamoDB
        orders = get_user_order_history_from_dynamodb()
        return render_template('admin_page.html', orders=orders)
    except Exception as e:
        flash(f'Error fetching orders: {e}', 'danger')
        return redirect(url_for('auth.admin_login'))  # Redirect if fetching orders fails