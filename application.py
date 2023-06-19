import joke
import os
from flask import Flask, redirect, request
from flask import jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
import requests

# Setting up the flask app, database, and environment variables
app = Flask(__name__)
load_dotenv()
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
client = MongoClient(
  f'mongodb+srv://{os.environ.get("DB_USERNAME")}:{os.environ.get("DB_PASSWORD")}@cluster0.ziyuaoy.mongodb.net/?retryWrites=true&w=majority'
)
db = client['StravaJokes']
collection = db['users']

# Standard Start Route
@app.route('/')
def api_root():
  return 'Welcome'

# Login Route (redirects to Strava's auth)
@app.route('/login')
def login():
  client_id = os.environ.get('CLIENT_ID')
  redirect_uri = 'https://stravajokesv2.beelauuu.repl.co/callback'
  scopes = 'activity:write,activity:read_all'
  authorization_url = f'https://www.strava.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}'
  return redirect(authorization_url)

# Callback route after authenticating
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
  # Parsing and storing token from response 
  response = requests.post(token_url, data=payload)
  data = response.json()
  # Checking for a valid response   
  if 'access_token' in data:
    access_token = data['access_token']
    refresh_token = data['refresh_token']
    user_id = data['athlete']['id']
    existing_user = collection.find_one({'user_id': user_id})

    # Store tokens in MongoDB (if user DNE)
    if existing_user == None:
      user_tokens = {
        'user_id': user_id,
        'access_token': access_token,
        'refresh_token': refresh_token
      }
      collection.insert_one(user_tokens)

    # Create a POST subscription for the webhook
    subscription_url = 'https://www.strava.com/api/v3/push_subscriptions'
    subscription_payload = {
      'client_id': os.environ.get('CLIENT_ID'),
      'client_secret': os.environ.get('CLIENT_SECRET'),
      'callback_url': 'https://stravajokesv2.beelauuu.repl.co/webhook',
      'verify_token': 'BEELAU'
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    subscription_response = requests.post(subscription_url,
                                          data=subscription_payload,
                                          headers=headers)

    # Check the response status code to ensure the subscription was created successfully
    if subscription_response.status_code == 201:
      # Subscription created successfully
      return jsonify({'message': 'Subscription created'}), 200
    else:
      # Failed to create subscription
      return jsonify({'message': 'Failed to create subscription. Most likely you are already subscribed'}), 500
  else:
    # Failed to obtain access token
    return jsonify({'message': 'Failed to obtain access token'}), 500


# Creates the endpoint for our webhook
@app.route('/webhook', methods=['POST'])
async def webhook():
  #Catching the webhook events & information  
  print("Webhook event received!", request.args, request.json)
  #If an activity is created, run the joke update function  
  if request.json['aspect_type'] == 'create' and request.json[
      'object_type'] == 'activity':
    await joke.update_joke(request.json['owner_id'])
    return 'JOKE_RECEIVED', 200
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

# For some reason, need to include the 0.0.0.0 for it to work.
if __name__ == '__main__':
  app.run('0.0.0.0')
