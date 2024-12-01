import boto3
from botocore.exceptions import ClientError
import os
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

# DynamoDB setup
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
dynamodb_resource = boto3.resource('dynamodb')

# Table references
orders_table = dynamodb_resource.Table('Orders')
products_table = dynamodb_resource.Table('Products')

# Create Products table
def create_products_table():
    try:
        existing_tables = dynamodb_client.list_tables()['TableNames']
        if 'Products' in existing_tables:
            print("Table 'Products' already exists")
            return

        table = dynamodb_resource.create_table(
            TableName='Products',
            KeySchema=[{'AttributeName': 'ProductID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'ProductID', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )

        table.wait_until_exists()
        print("Table 'Products' created successfully!")
    except ClientError as e:
        print("Error creating Products table:", e.response['Error']['Message'])

# Add product to Products table
def add_product_to_dynamodb(product_id, product_name, description, price, quantity, image_url):
    try:
        response = products_table.put_item(
            Item={
                'ProductID': product_id,
                'ProductName': product_name,
                'Description': description,
                'Price': price,
                'Quantity': quantity,
                'ImageURL': image_url
            }
        )
        return response
    except ClientError as e:
        print("Error adding product:", e.response['Error']['Message'])
        return None

# Get products from Products table
def get_products_from_dynamodb():
    try:
        response = products_table.scan()
        return response.get('Items', [])
    except ClientError as e:
        print("Error retrieving products:", e.response['Error']['Message'])
        return []

# Create Orders table (Updated with secondary index for UserID)
def create_orders_table():
    try:
        existing_tables = dynamodb_client.list_tables()['TableNames']
        if 'Orders' in existing_tables:
            print("Table 'Orders' already exists")
            return

        table = dynamodb_resource.create_table(
            TableName='Orders',
            KeySchema=[{'AttributeName': 'OrderID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'OrderID', 'AttributeType': 'S'},
                                  {'AttributeName': 'UserID', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserID-index',
                    'KeySchema': [{'AttributeName': 'UserID', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ]
        )

        table.wait_until_exists()
        print("Table 'Orders' created successfully!")
    except ClientError as e:
        print("Error creating Orders table:", e.response['Error']['Message'])


# Place an order
def place_order(user_id, product_id, quantity):
    try:
        order_id = str(uuid.uuid4())
        order_date = datetime.utcnow().isoformat()

        response = orders_table.put_item(
            Item={
                'OrderID': order_id,
                'UserID': user_id,
                'ProductID': product_id,
                'Quantity': quantity,
                'OrderDate': order_date,
                'OrderStatus': 'Pending'
            }
        )
        print(f"Order {order_id} placed successfully!")
        return {'OrderID': order_id}
    except ClientError as e:
        print("Error placing order:", e.response['Error']['Message'])
        return None

# Fix for querying orders
def get_user_order_history_from_dynamodb(user_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('orders')

    try:
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error fetching orders: {e}")
        raise Exception('Unable to fetch orders')
    
def get_all_orders_from_dynamodb():
    try:
        response = orders_table.scan()  # Fetch all items from the table
        return response.get('Items', [])  # Return a list of orders
    except Exception as e:
        print(f"Error fetching orders: {e}")
        raise
