import json
import urllib3
import base64
import os

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

        # Construct the URL
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

        # Check if orderCount > 0 and get lifetimeValue
        if order_count > 0:
            result = {
                "lifetimeValue": lifetime_value
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
