from datetime import datetime, time
import json
import uuid
import boto3
from flask import Blueprint, Flask, jsonify, render_template, request, redirect, session, url_for, flash
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, ClientError
import os
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from cognito import register_user, login_user, forgot_password, verify_user, verify_token
from boto3.dynamodb.conditions import Key
from lambda_function.lambda_function import lambda_handler
from mobile_sales.tracker import MobileSalesTracker
from dynamo import (
    add_product_to_dynamodb, 
    create_products_table, 
    create_orders_table,
    get_user_order_history_from_dynamodb, 
    place_order, 
    get_products_from_dynamodb,
    get_all_orders_from_dynamodb
)

sns_client = boto3.client("sns", region_name="us-east-1")  # Replace with your region
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:764036388996:OrderStatusUpdates"  # Replace with your ARN

admin_routes = Blueprint("admin_routes", __name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

# Load environment variables
load_dotenv()  
AWS_REGION = os.getenv('AWS_REGION')
USER_POOL_ID = os.getenv('USER_POOL_ID')
CLIENT_ID = os.getenv('CLIENT_ID')

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Products')

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table('Orders')

# Create tables in DynamoDB
create_products_table()
create_orders_table()

# Add initial products with S3 URLs to DynamoDB
products = [
    {
        "product_id": "1",
        "product_name": "iPhone 14 Pro",
        "description": "A16 Bionic chip, Dynamic Island, Pro Camera System.",
        "price": 999,
        "quantity": 10,
        "image_url": "https://my-tracking-products-images.s3.us-east-1.amazonaws.com/iphone14pro.jpg"
    },
    {
        "product_id": "2",
        "product_name": "Samsung Galaxy S23 Ultra",
        "description": "200 MP camera, Snapdragon 8 Gen 2 processor.",
        "price": 1199,
        "quantity": 15,
        "image_url": "https://my-tracking-products-images.s3.us-east-1.amazonaws.com/samsung-s23.jpg"
    },
    {
        "product_id": "3",
        "product_name": "Google Pixel 7 Pro",
        "description": "Tensor G2 chip, AI-powered camera, and more.",
        "price": 899,
        "quantity": 20,
        "image_url": "https://my-tracking-products-images.s3.us-east-1.amazonaws.com/pixel7pro.jpg"
    },
    {
        "product_id": "4",
        "product_name": "OnePlus 11",
        "description": "Snapdragon 8 Gen 2, Hasselblad-tuned cameras.",
        "price": 799,
        "quantity": 25,
        "image_url": "https://my-tracking-products-images.s3.us-east-1.amazonaws.com/oneplus11.jpg"
    },
    {
        "product_id": "5",
        "product_name": "Xiaomi 13 Pro",
        "description": "Leica cameras, Snapdragon 8 Gen 2 processor.",
        "price": 749,
        "quantity": 30,
        "image_url": "https://my-tracking-products-images.s3.us-east-1.amazonaws.com/xiaomi13pro.jpg"
    }
]

for product in products:
    add_product_to_dynamodb(
        product_id=product["product_id"],
        product_name=product["product_name"],
        description=product["description"],
        price=product["price"],
        quantity=product["quantity"],
        image_url=product["image_url"]  # Use pre-uploaded S3 URL
    )

print("Initial products added to DynamoDB!")


def get_products_from_dynamodb():
    try:
        response = table.scan()  # Scan all products from the DynamoDB table
        return response['Items']
    except NoCredentialsError:
        flash("Credentials not found. Please check your AWS setup.", 'danger')
        return []
    
@app.route('/place_order/<product_id>', methods=['POST'])
def place_order_route(product_id):
    # COMMENT: Added functionality to place an order from frontend
    user_id = session.get('username')
    if not user_id:
        flash('Please log in to place an order.', 'warning')
        return redirect(url_for('login'))

    quantity = request.form.get('quantity', 1)  # Default to 1 if not specified
    order_result = place_order(user_id, product_id, int(quantity))

    if order_result:
        flash(f"Order placed successfully! Order ID: {order_result['OrderID']}", 'success')
    else:
        flash('Failed to place order. Please try again.', 'danger')
    return redirect(url_for('home'))

@app.route('/order_history', methods=['GET'])
def order_history():
    # Assuming the user is logged in and you can get the user_id from the session
    user_id = session.get('username')  # Replace 'username' with your session key

    if not user_id:
        return jsonify({'message': 'User not logged in'}), 401

    try:
        # Scan the table for all orders and filter by UserID
        response = orders_table.scan(
            FilterExpression=Key('UserID').eq(user_id)
        )

        # Extract items from the response
        orders = response.get('Items', [])

        # Format data for the frontend
        formatted_orders = [
            {
                'OrderID': order['OrderID'],
                'ProductID': order['ProductID'],
                'OrderStatus': order.get('OrderStatus', 'Pending'),  # Default to 'Pending'
                'OrderDate': order['OrderDate']
            }
            for order in orders
        ]

        return jsonify(formatted_orders), 200

    except ClientError as e:
        print(f"Error fetching order history: {e}")
        return jsonify({'message': 'Error fetching order history'}), 500
    
@app.route('/buy', methods=['POST'])
def buy_product():
    try:
        # Get data from the frontend (product_id and user_id)
        data = request.get_json()
        product_id = data['product_id']
        user_id = data['user_id']
        
        # You may fetch product details from DynamoDB if needed for order details
        #product = get_products_from_dynamodb(product_id)  # Implement this if necessary

        # Generate unique order ID and timestamp
        order_id = str(uuid.uuid4())
        order_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        # Save the order to DynamoDB
        response = orders_table.put_item(
            Item={
                'OrderID': order_id,
                'UserID': user_id,
                'ProductID': product_id,
                'OrderStatus': 'Pending',  # Can update this later
                'OrderDate': order_date,  # Replace with actual date if needed
            }
        )

        # Return success message
        return jsonify({'message': 'Order placed successfully!'}), 200

    except Exception as e:
        print(f"Error placing order: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route for the home page (Product Store)
@app.route('/')
def home():
    # Fetch product data
    products_data = get_products_from_dynamodb()

    # Fetch the user ID from the session
    user_id = session.get('username', None)
    if user_id is None:
        flash('Please log in to view this page.', 'warning')
        return redirect(url_for('login'))

    # Pass products data to the template
    return render_template('index.html', products=products_data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        auth_result = login_user(username, password)
        if isinstance(auth_result, dict):  # Successful login
            session['username'] = username
            session['password'] = password
            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to home page
        else:
            flash(auth_result, 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        register_result = register_user(username, email, password)
        if 'CodeDeliveryDetails' in register_result:
            flash('Registration successful! Please check your email for verification.', 'success')
            return redirect(url_for('login'))
        else:
            flash(register_result, 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the session to log the user out
    flash('You have been logged out.', 'info')
    session.clear()
    return redirect(url_for('login'))  # Redirect to login page after logout


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_route():
    if request.method == 'POST':
        email = request.form.get('email')
        result = forgot_password(email)
        if 'CodeDeliveryDetails' in result:
            flash('A reset code has been sent to your email.', 'success')
        else:
            flash(result, 'danger')
        return redirect(url_for('forgot_password_route'))

    return render_template('forgot_password.html')


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        username = request.form.get('username')
        verification_code = request.form.get('verification_code')

        verification_result = verify_user(username, verification_code)
        if verification_result == "SUCCESS":
            flash('Account verified successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(verification_result, 'danger')
            return redirect(url_for('verify'))

    return render_template('verify.html')

def authenticate_user(username, password):
    try:
        # Use the initiate_auth API to authenticate the user
        response = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        # If authentication is successful, the response will contain tokens
        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']
        
        # Store the tokens or perform additional logic as needed
        # For example, store the id_token in session
        return True  # User authenticated successfully
    except ClientError as e:
        # Handle errors (e.g., incorrect credentials)
        print(f"Error authenticating user: {e}")
        return False  # Authentication failed

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Authenticate user with Cognito
        try:
            response = cognito_client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                ClientId=CLIENT_ID,
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )

            # If authentication is successful, Cognito returns IdToken and AccessToken
            id_token = response['AuthenticationResult']['IdToken']
            access_token = response['AuthenticationResult']['AccessToken']
            refresh_token = response['AuthenticationResult']['RefreshToken']

            # Store tokens and admin flag in session
            session['id_token'] = id_token
            session['access_token'] = access_token
            session['refresh_token'] = refresh_token
            session['admin'] = True  # Set admin session flag

            # Redirect to the admin dashboard
            return redirect(url_for('admin_page'))

        except ClientError as e:
            flash('Invalid credentials. Please try again.', 'danger')
            print(f"Error during login: {e}")
            return render_template('admin_login.html')

    return render_template('admin_login.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if not session.get('admin'):
        flash('You must log in to access the admin page.', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'GET':
        try:
            orders = get_all_orders_from_dynamodb()
            return render_template('admin_page.html', orders=orders)
        except Exception as e:
            flash(f"Error fetching orders: {e}", 'danger')
            return redirect(url_for('admin_login'))

    elif request.method == 'POST':
        try:
            order_id = request.form.get('order_id')
            new_status = request.form.get('status')
            user_email = request.form.get('user_email')

            if update_order_status(order_id, new_status):
                payload = {
                    "order_id": order_id,
                    "status": new_status,
                    "user_email": user_email,
                }
                lambda_response = invoke_lambda_function("OrderStatusNotification", payload)
                if lambda_response.get("statusCode") == 200:
                    flash(f"Order {order_id} updated to {new_status}. Notification sent.", "success")
                else:
                    flash(f"Order updated but failed to notify user: {lambda_response.get('body')}", 'warning')
            else:
                flash(f"Failed to update order {order_id} in the database.", 'danger')

        except Exception as e:
            flash(f"Error updating order: {e}", 'danger')

        return redirect(url_for('admin_page'))

    
def update_order_status(order_id, new_status):
    try:
        table = dynamodb.Table('Orders')  # Ensure this is the correct table name
        
        # Update order status in the Orders table
        response = table.update_item(
            Key={'OrderID': order_id},  # Use the correct primary key
            UpdateExpression="set OrderStatus = :status",  # Ensure correct attribute name
            ExpressionAttributeValues={
                ':status': new_status
            },
            ReturnValues="UPDATED_NEW"
        )
        
        # Debugging response for successful status update
        print(f"Order status updated in Orders table: {response}")
        return True  # Indicate successful update
    except Exception as e:
        print(f"Error updating order status: {e}")
        return False  # Indicate failure to update

def invoke_lambda_function(function_name, payload):
    """
    Invoke a Lambda function programmatically.
    """
    client = boto3.client('lambda')
    try:
        response = client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload),
        )
        response_payload = json.loads(response['Payload'].read())
        if response.get("StatusCode") != 200:
            raise Exception(f"Lambda invocation failed: {response_payload}")
        print(f"Lambda response: {response_payload}")
        return response_payload
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
    
@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    # Pass the correct argument name
    tracker = MobileSalesTracker(dynamodb_orders_table_name="Orders")
    tracker.fetch_sales_from_dynamodb()

    sorted_sales = tracker.sales  # Fetch sorted sales data

    return render_template(
        'admin_stats.html',
        sorted_sales=sorted_sales,
    )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
