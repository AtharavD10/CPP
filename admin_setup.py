import boto3

def create_admin_user():
    # Initialize Cognito client
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

    try:
        # Step 1: Create the admin user with a temporary password
        response = cognito_client.admin_create_user(
            UserPoolId='us-east-1_Y4dXGlR6q',  # Replace with your Cognito User Pool ID
            Username='atharavd10@gmail.com',
            UserAttributes=[
                {'Name': 'email', 'Value': 'atharavd10@gmail.com'},
                {'Name': 'custom:isAdmin', 'Value': 'true'},  # Add the isAdmin attribute
            ],
            TemporaryPassword='Admin@10'  # Temporary password for the admin
        )
        print("Admin user created with temporary password:", response)

        # Step 2: Set a permanent password (without requiring user to change it)
        permanent_password = 'Leomessi*10'  # Set your desired permanent password

        # Set the permanent password
        password_response = cognito_client.admin_set_user_password(
            UserPoolId='us-east-1_Y4dXGlR6q',  # Replace with your Cognito User Pool ID
            Username='atharavd10@gmail.com',
            Password=permanent_password,
            Permanent=True  # Mark the password as permanent
        )
        print("Permanent password set:", password_response)

    except Exception as e:
        print("Error creating admin user:", str(e))

if __name__ == "__main__":
    create_admin_user()
