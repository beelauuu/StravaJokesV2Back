import joke
import os
from flask import Flask, redirect, request
from flask import jsonify
from dotenv import load_dotenv
import requests

app = Flask(__name__)
load_dotenv()
client_id=os.environ.get('CLIENT_ID'),
client_secret=os.environ.get('CLIENT_SECRET'),
refresh_token=os.environ.get('REFRESH_TOKEN')

@app.route('/')
def api_root():
    return 'This means it is working :)'

@app.route('/login')
def login():
    client_id = os.environ.get('CLIENT_ID')
    redirect_uri = 'http://127.0.0.1:5000/callback'
    scopes = 'activity:write,activity:read_all'  # Adjust the scopes according to your requirements
    authorization_url = f'https://www.strava.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}'
    return redirect(authorization_url)

import requests
from flask import redirect, jsonify, request

@app.route('/callback')
def strava_callback():
    code = request.args.get('code')
    # Exchange the authorization code for an access token
    token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': os.environ.get('CLIENT_ID'),
        'client_secret': os.environ.get('CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(token_url, data=payload)
    data = response.json()

    if 'access_token' in data:
        access_token = data['access_token']
        refresh_token = data['refresh_token']
        
        # Store the access_token and refresh_token securely and associate them with the authenticated user
        # This step depends on your application's data storage and user management system
        
        # Create a push subscription for the authenticated user
        subscription_url = 'https://www.strava.com/api/v3/push_subscriptions'
        subscription_payload = {
            'client_id': os.environ.get('CLIENT_ID'),
            'client_secret': os.environ.get('CLIENT_SECRET'),
            'callback_url': 'http://127.0.0.1:5000/webhook',
            'verify_token': 'BEELAU'
        }
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        subscription_response = requests.post(subscription_url, data=subscription_payload, headers=headers)
        print(subscription_response.json())
        # Check the response status code to ensure the subscription was created successfully
        if subscription_response.status_code == 201:
            # Subscription created successfully
            return jsonify({'message': 'Subscription created'}), 200
        else:
            # Failed to create subscription
            return jsonify({'message': 'Failed to create subscription'}), 500
    else:
        # Failed to obtain access token
        return jsonify({'message': 'Failed to obtain access token'}), 500



# Creates the endpoint for our webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    print("Webhook event received!", request.args, request.json)
    return 'EVENT_RECEIVED', 200

# Adds support for GET requests to our webhook
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    # Your verify token. Should be a random string.
    VERIFY_TOKEN = "BEELAU"
    # Parses the query params
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # Checks if a token and mode is in the query string of the request
    if mode and token:
        # Verifies that the mode and token sent are valid
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            # Responds with the challenge token from the request
            print('WEBHOOK_VERIFIED')
            return jsonify({'hub.challenge': challenge}), 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            return 'Forbidden', 403
    return 'Bad Request', 400
        
if __name__ == '__main__':
    app.run(debug=True)