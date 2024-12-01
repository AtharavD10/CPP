import boto3

AWS_REGION = "us-east-1"  # Replace with your region
SNS_TOPIC_NAME = "OrderStatusUpdates"
LAMBDA_ROLE_ARN = "arn:aws:iam::764036388996:role/LabRole"  # Replace with your Lambda role ARN

sns_client = boto3.client("sns", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)
iam_client = boto3.client("iam", region_name=AWS_REGION)

def create_sns_topic():
    response = sns_client.create_topic(Name=SNS_TOPIC_NAME)
    topic_arn = response["TopicArn"]
    print(f"SNS Topic created: {topic_arn}")
    return topic_arn

def create_lambda_function():
    with open("lambda_function/lambda_function.zip", "rb") as f:
        zipped_code = f.read()

    response = lambda_client.create_function(
        FunctionName="OrderStatusNotification",
        Runtime="python3.8",
        Role=LAMBDA_ROLE_ARN,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zipped_code},
        Timeout=15,
    )
    print(f"Lambda Function created: {response['FunctionArn']}")
    return response["FunctionArn"]

def subscribe_lambda_to_sns(topic_arn, lambda_arn):
    lambda_client.add_permission(
        FunctionName="OrderStatusNotification",
        StatementId="SNSInvoke",
        Action="lambda:InvokeFunction",
        Principal="sns.amazonaws.com",
        SourceArn=topic_arn,
    )
    sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol="lambda",
        Endpoint=lambda_arn,
    )
    print("Lambda subscribed to SNS topic.")

if __name__ == "__main__":
    sns_topic_arn = create_sns_topic()
    lambda_function_arn = create_lambda_function()
    subscribe_lambda_to_sns(sns_topic_arn, lambda_function_arn)
