import boto3
from botocore.exceptions import ClientError
import os

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')

AWS_BUCKET_NAME = "my-tracking-products-images"  # Replace with your actual S3 bucket name

s3_client = boto3.client("s3", region_name=AWS_REGION)

def bucket_exists(bucket_name):
    """
    Checks if an S3 bucket exists by listing all buckets.
    :param bucket_name: Name of the bucket to check
    :return: True if the bucket exists, False otherwise
    """
    try:
        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
        return bucket_name in buckets
    except ClientError as e:
        print(f"Error listing buckets: {e}")
        return False

def create_bucket(bucket_name=AWS_BUCKET_NAME):
    """
    Creates an S3 bucket if it doesn't already exist.
    """
    if bucket_exists(bucket_name):
        print(f"Bucket '{bucket_name}' already exists.")
        return

    try:
        if not AWS_REGION:  # Ensure AWS_REGION is not None
            raise ValueError("AWS_REGION is not set. Please set it in your environment variables or .env file.")

        if AWS_REGION == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
            )
        print(f"Bucket '{bucket_name}' created successfully.")
    except ClientError as ce:
        print(f"Error creating bucket: {ce}")
        raise
    except ValueError as ve:
        print(f"Configuration error: {ve}")
        raise


def upload_image_to_s3(bucket_name, file_name, object_name=None):
    """
    Uploads a file to an S3 bucket.
    :param bucket_name: Name of the bucket
    :param file_name: Local path of the file to upload
    :param object_name: S3 object name (optional, defaults to file_name)
    """
    if object_name is None:
        object_name = file_name.split('/')[-1]  # Use file name as the object name

    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
        s3_url = f"https://{bucket_name}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
        print(f"File uploaded successfully. S3 URL: {s3_url}")
        return s3_url
    except ClientError as e:
        print(f"Error uploading file: {e}")
        raise
