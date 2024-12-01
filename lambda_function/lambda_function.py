import json
import boto3

dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
ORDERS_TABLE = "Orders"  # Replace with your DynamoDB table name

sns_client = boto3.client("sns", region_name='us-east-1')
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:764036388996:OrderStatusUpdates"  # Replace with your SNS Topic ARN

# import json
# import boto3

# dynamodb = boto3.resource("dynamodb")
# ORDERS_TABLE = "Orders"  # Replace with your DynamoDB table name

# sns_client = boto3.client("sns")
# SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:764036388996:OrderStatusUpdates"  # Replace with your SNS Topic ARN

def lambda_handler(event, context):
    try:
        # Check if the event is from SNS
        if "Records" in event and "Sns" in event["Records"][0]:
            sns_message = event["Records"][0]["Sns"]
            message = json.loads(sns_message["Message"])

            order_id = message.get("order_id")
            status = message.get("status")
            user_email = message.get("user_email")

        # Handle direct invocation (non-SNS)
        elif all(key in event for key in ["order_id", "status", "user_email"]):
            order_id = event["order_id"]
            status = event["status"]
            user_email = event["user_email"]

        else:
            print("Invalid event structure received.")
            return {"statusCode": 400, "body": "Invalid event structure"}

        # Update order status in DynamoDB
        table = dynamodb.Table(ORDERS_TABLE)
        table.update_item(
            Key={"OrderID": order_id},
            UpdateExpression="SET OrderStatus = :status",
            ExpressionAttributeValues={":status": status},
        )
        print(f"Order {order_id} updated to status: {status}")

        # Send email notification via SNS
        subject = f"Your Order {order_id} Status Updated"
        body = f"Dear customer,\n\nYour order with ID {order_id} has been updated to '{status}'.\n\nThank you for shopping with us."
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=body,
            Subject=subject,
        )
        print(f"Email sent successfully to {user_email} with order status update.")

        return {"statusCode": 200, "body": "Order updated and email sent."}

    except Exception as e:
        print(f"Error in Lambda function: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}


    except Exception as e:
        print(f"Error in Lambda function: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
