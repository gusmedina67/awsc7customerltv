import json
import urllib3
import base64
import os
import time
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler_get(event, context):
    try:
        # Extract customer_guid and tenant from the event
        customer_guid = event['pathParameters'].get('customer_guid')
        tenant = event['pathParameters'].get('tenant')
        
        if not customer_guid:
            raise ValueError("customer_guid is required.")
        if not tenant:
            raise ValueError("tenant is required.")

        # Fetch API credentials from environment variables
        user_id = os.environ['USER_ID']
        password = os.environ['PASSWORD']

        if not user_id or not password:
            raise ValueError("Environment variables USER_ID and PASSWORD must be set.")

        # Initialize DynamoDB client
        dynamodb_client = boto3.client('dynamodb')

        # Fetch 'LTV_TITLE' setting from DynamoDB
        try:
            ltv_title_response = dynamodb_client.get_item(
                TableName='SystemSettings',
                Key={
                    'SettingKey': {'S': 'LTV_TITLE'},
                    'Tenant': {'S': tenant}
                }
            )
            ltv_title_value = ltv_title_response.get('Item', {}).get('SettingValue', {}).get('S', 'Default Title')
        except ClientError as e:
            raise ValueError(f"Error fetching 'LTV_TITLE' from DynamoDB: {str(e)}")

        # Fetch 'LTV_PERCENTAGE' setting from DynamoDB
        try:
            ltv_percentage_response = dynamodb_client.get_item(
                TableName='SystemSettings',
                Key={
                    'SettingKey': {'S': 'LTV_PERCENTAGE'},
                    'Tenant': {'S': tenant}
                }
            )
            ltv_percentage_value = ltv_percentage_response.get('Item', {}).get('SettingValue', {}).get('N', '0')
            # print("LTV Percentage Response:", ltv_percentage_response)
            ltv_percentage = float(ltv_percentage_value) / 100  # Convert to percentage
        except ClientError as e:
            raise ValueError(f"Error fetching 'LTV_PERCENTAGE' from DynamoDB: {str(e)}")

        # Construct the URL for the external API
        url = f"https://api.commerce7.com/v1/customer/{customer_guid}"

        # Encode credentials for Basic Authentication
        auth_header = base64.b64encode(f"{user_id}:{password}".encode()).decode()

        # Initialize urllib3 HTTP client
        http = urllib3.PoolManager()

        # Make the GET request
        response = http.request(
            "GET",
            url,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json",
                "tenant": tenant
            },
            timeout=3.0
        )

        # Check the response status
        if response.status != 200:
            raise ValueError(f"API call failed with status {response.status}: {response.data.decode('utf-8')}")

        # Parse the response data
        response_data = json.loads(response.data.decode('utf-8'))

        # Extract order information
        order_info = response_data.get('orderInformation', {})
        order_count = order_info.get('orderCount', 0)
        lifetime_value = order_info.get('lifetimeValue', 0)

        # Apply the percentage calculation
        adjusted_lifetime_value = lifetime_value * ltv_percentage

        # Check if orderCount > 0 and include additional information
        if order_count > 0:
            result = {
                "title": ltv_title_value,
                "lifetimeValue": adjusted_lifetime_value
            }
        else:
            result = {
                "message": "Order count is 0 or less, no lifetime value available."
            }

        # Return the response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET"
            },
            "body": json.dumps(result)
        }

    except KeyError as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET"
            },
            "body": json.dumps({
                "message": f"Missing environment variable: {str(e)}"
            }),
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET"
            },
            "body": json.dumps({
                "message": str(e)
            }),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET"
            },
            "body": json.dumps({
                "message": "Error invoking the API",
                "error": str(e),
            }),
        }

def lambda_handler_activate(event, context):
    try:
        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)

        percentage = body.get('percentage')
        title = body.get('title')
        tenant_id = body.get('tenantId')
        user = body.get('user')

        if not all([percentage, title, tenant_id, user]):
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid input: percentage, title, tenantId, and user are required."})
            }

        # Get current timestamp in epoch format (seconds since Unix epoch)
        current_timestamp = int(time.time())  # Epoch time in seconds

        table_name = 'SystemSettings'
        table = dynamodb.Table(table_name)
        
        items = [
            {"SettingKey": "LTV_TITLE", "Tenant": tenant_id, "SettingValue": title},
            {"SettingKey": "LTV_PERCENTAGE", "Tenant": tenant_id, "SettingValue": Decimal(str(percentage))},
            {"SettingKey": "LTV_USER", "Tenant": tenant_id, "SettingValue": user},
            {"SettingKey": "LTV_USER_ACTIVE", "Tenant": tenant_id, "SettingValue": True},
            {"SettingKey": "LTV_ACTIVATION_TIMESTAMP", "Tenant": tenant_id, "SettingValue": Decimal(current_timestamp)}        
        ]

        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Items successfully inserted."})
        }
    except Exception as e:
        print("Error inserting items:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", "error": str(e)})
        }

def lambda_handler_deactivate(event, context):
    try:
        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)

        tenant_id = body.get('tenantId')

        if not tenant_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid input: tenantId is required."})
            }

        # Get current timestamp in epoch format
        current_timestamp = int(time.time())  # Epoch time in seconds

        table_name = 'SystemSettings'
        table = dynamodb.Table(table_name)

        # Add new entry for LTV_DEACTIVATION_TIMESTAMP
        items = [
            {"SettingKey": "LTV_DEACTIVATION_TIMESTAMP", "Tenant": tenant_id, "SettingValue": Decimal(current_timestamp)},
            {"SettingKey": "LTV_USER_ACTIVE", "Tenant": tenant_id, "SettingValue": False}
        ]

        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Deactivation successful."})
        }
    except Exception as e:
        print("Error deactivating:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", "error": str(e)})
        }
        