import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

class MobileSalesTracker:
    def __init__(self, dynamodb_orders_table_name):
        """
        Initialize the tracker with the DynamoDB table name for orders.
        :param dynamodb_orders_table_name: Name of the DynamoDB orders table.
        """
        dynamodb = boto3.resource("dynamodb")
        self.orders_table = dynamodb.Table(dynamodb_orders_table_name)
        self.sales = []  # Will store sorted sales data

    def fetch_sales_from_dynamodb(self):
        """
        Fetch sales data from the DynamoDB orders table and calculate total orders by ProductID.
        Assumes the orders table contains fields: 'OrderID', 'ProductID', 'OrderStatus'.
        """
        if not self.orders_table:
            raise ValueError("DynamoDB Orders table is not set.")

        # Scan the Orders table to retrieve all items
        response = self.orders_table.scan()
        order_items = response.get("Items", [])

        if not order_items:
            print("No orders found in DynamoDB.")
            return

        # Dictionary to count orders per ProductID
        sales_data = {}

        # Define valid statuses for counting orders
        valid_statuses = {"Order Confirmed", "Dispatched", "Delivered"}

        for order in order_items:
            product_id = order.get("ProductID")
            order_status = order.get("OrderStatus")

            # Only count orders with a valid status
            if not product_id or order_status not in valid_statuses:
                continue

            # Increment count for the product
            if product_id in sales_data:
                sales_data[product_id] += 1
            else:
                sales_data[product_id] = 1

        # Store the sorted sales data for further processing
        self.sales = sorted(sales_data.items(), key=lambda x: x[0])  # Sort by ProductID
        print(f"Sales data fetched and sorted: {self.sales}")

    def total_sales(self):
        """
        Calculate total number of products sold and group by ProductID.
        Returns a dictionary with ProductID as the key and order count as the value.
        """
        total_orders = {product_id: total for product_id, total in self.sales}
        print(f"Total sales by product: {total_orders}")  # Debugging print statement
        return total_orders
