

#def create_user_pool():
    # Create the Cognito Identity Provider (IDP) client
    #client = boto3.client('cognito-idp', region_name='us-east-1')  # Replace 'your-region' with your AWS region

    #try:
        # Step 1: Create the User Pool
        #user_pool_response = client.create_user_pool(
            #PoolName="MyTrackingAppUserPool",
            #AutoVerifiedAttributes=['email'],  # Automatically verify email
            #Policies={
                #"PasswordPolicy": {
                   # "MinimumLength": 8,
                  #  "RequireUppercase": True,
                    #"RequireLowercase": True,
                    #"RequireNumbers": True,
                  #  "RequireSymbols": False,
                   # "TemporaryPasswordValidityDays": 7
              #  }
           # },
            #Schema=[
               # {
                    #"Name": "email",
                    #"AttributeDataType": "String",
                   # "Required": True
               # }
           # ]
        #)
        #user_pool_id = user_pool_response['UserPool']['Id']
       # print(f"User Pool created successfully with ID: {user_pool_id}")

        # Step 2: Create the App Client
        #app_client_response = client.create_user_pool_client(
           # UserPoolId=user_pool_id,
            #ClientName="MyTrackingAppClient",
            #GenerateSecret=False,  # No client secret for browser-based apps
           # ExplicitAuthFlows=['ALLOW_USER_PASSWORD_AUTH', 'ALLOW_REFRESH_TOKEN_AUTH']
        #)
       # app_client_id = app_client_response['UserPoolClient']['ClientId']
       # print(f"App Client created successfully with ID: {app_client_id}")

       # return {
            #"UserPoolId": user_pool_id,
            #"AppClientId": app_client_id
      #  }

   # except Exception as e:
       # print(f"An error occurred: {e}")
      #  return None


#if __name__ == "__main__":
   # result = create_user_pool()
   # if result:
       # print(f"User Pool ID: {result['UserPoolId']}")
       # print(f"App Client ID: {result['AppClientId']}")

import boto3
from botocore.exceptions import ClientError
import os

# Load the Cognito User Pool ID and Client ID from environment variables or directly
USER_POOL_ID = os.getenv("USER_POOL_ID")
CLIENT_ID = os.getenv("CLIENT_ID")

# Initialize the Cognito client
cognito_client = boto3.client('cognito-idp', region_name="us-east-1")  # Adjust the region if needed

def register_user(username, email, password):
    try:
        # Sign up the user
        response = cognito_client.sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
            ],
        )

        # Automatically confirm the user
        cognito_client.admin_confirm_sign_up(
            UserPoolId=USER_POOL_ID,
            Username=username,
        )

        # Set email_verified to true
        cognito_client.admin_update_user_attributes(
            UserPoolId=USER_POOL_ID,
            Username=username,
            UserAttributes=[
                {"Name": "email_verified", "Value": "true"},
            ],
        )
        return {"success": True, "message": "User registered and email auto-verified successfully."}
    except cognito_client.exceptions.UsernameExistsException:
        return {"success": False, "message": "This username is already taken."}
    except Exception as e:
        return {"success": False, "message": str(e)}



def login_user(username, password):
    try:
        response = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        return response['AuthenticationResult']
    except ClientError as e:
        return e.response['Error']['Message']

def forgot_password(email):
    try:
        response = cognito_client.forgot_password(
            ClientId=CLIENT_ID,
            Username=email
        )
        return response
    except ClientError as e:
        return e.response['Error']['Message']

def verify_user(username, verification_code):
    try:
        response = cognito_client.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=username,
            ConfirmationCode=verification_code,
            Password='newpassword123'  # You can modify to allow a user to set their password
        )
        return response
    except ClientError as e:
        return e.response['Error']['Message']

def verify_token(id_token):
    try:
        response = cognito_client.get_user(
            AccessToken=id_token  # AWS Cognito uses access token for user authentication
        )
        return response
    except ClientError as e:
        return None  # If authentication fails or token is invalid
