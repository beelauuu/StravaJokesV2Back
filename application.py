import joke
import os
from flask import Flask, redirect, request
from flask import jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
from urllib.parse import quote

app = Flask(__name__)
load_dotenv()
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
client = MongoClient(
  f'mongodb+srv://{os.environ.get("DB_USERNAME")}:{os.environ.get("DB_PASSWORD")}@cluster0.ziyuaoy.mongodb.net/?retryWrites=true&w=majority'
)
db = client['StravaJokes']
collection = db['users']


@app.route('/login')
def login():
  # Redirects to Strava authorization
  client_id = os.environ.get('CLIENT_ID')
  redirect_uri = 'https://stravajokesv2.beelauuu.repl.co/create_callback'
  scopes = 'activity:write,activity:read_all'
  authorization_url = f'https://www.strava.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}'
  return redirect(authorization_url)

# Yeah these 2 routes are commented out on prod because they could cause problems if
# just anybody could go ahead and create/delete webhooks. I'll leave them here
# for now just in case shit hits the fan.

@app.route('/create_webhook')
def create_webhook():
  # Create a push subscription for the webhook (no subscribers)
  subscription_url = 'https://www.strava.com/api/v3/push_subscriptions'
  subscription_payload = {
    'client_id': os.environ.get('CLIENT_ID'),
    'client_secret': os.environ.get('CLIENT_SECRET'),
    'callback_url': 'https://stravajokesv2.beelauuu.repl.co/webhook',
    'verify_token': 'BEELAU'
  }
  subscription_response = requests.post(subscription_url,
                                        data=subscription_payload)

  # Check the response status code to ensure the subscription was created successfully
  if subscription_response.status_code == 201:
    # Subscription created successfully
    return redirect("https://jokepy.vercel.app/message?message=" +
                    quote("Subsciption Created!"))
  else:
    # Failed to create subscription
    return redirect("https://jokepy.vercel.app/message?message=" +
                    quote("Failed to create subscription"))


@app.route('/delete_webhook')
def delete_webhook():
  # Getting the webhook subscription id
  url = 'https://www.strava.com/api/v3/push_subscriptions'
  params = {
    'client_id': os.getenv('CLIENT_ID'),
    'client_secret': os.getenv('CLIENT_SECRET')
  }
  response = requests.get(url, params=params)
  data = response.json()

  # If found, then delete the webhook
  if 'id' in data[0]:
    subscription_id = data[0]['id']
    delete_url = f'https://www.strava.com/api/v3/push_subscriptions/{subscription_id}'
    params = {
      'client_id': os.getenv('CLIENT_ID'),
      'client_secret': os.getenv('CLIENT_SECRET')
    }
    response = requests.delete(delete_url, params=params)
    client.drop_database('StravaJokes')

    if response.status_code == 204 or response.status_code == 200:
      return redirect("https://jokepy.vercel.app/message?message=" +
                      quote("Deleted successfully! Subscription ID: " +
                            str(subscription_id)))
    else:
      return redirect("https://jokepy.vercel.app/message?message=" +
                      quote("Failed To Delete Webhook!"))
  else:
    return redirect("https://jokepy.vercel.app/message?message=" +
                    quote("Failed To Find Webhook!"))


@app.route('/create_callback')
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
    user_id = data['athlete']['id']
    existing_user = collection.find_one({'user_id': user_id})
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    callback_url = 'https://stravajokesv2.beelauuu.repl.co/webhook'
    verify_token = 'BEELAU'

    # Create a push subscription to the webhook
    subscription_url = 'https://www.strava.com/api/v3/push_subscriptions'
    subscription_payload = {
      'client_id': client_id,
      'client_secret': client_secret,
      'callback_url': callback_url,
      'verify_token': verify_token,
      'access_token': access_token
    }
    subscription_response = requests.post(subscription_url,
                                          data=subscription_payload)
    # Check the response status code to ensure the subscription was created successfully
    if subscription_response.status_code == 201 or subscription_response.status_code == 400:
      user_tokens = {
        'user_id': user_id,
        'access_token': access_token,
        'refresh_token': refresh_token,
      }
      # Store tokens in MongoDB (if user DNE)
      if existing_user is None:
        collection.insert_one(user_tokens)
      return redirect("https://jokepy.vercel.app/message?message=" +
                      quote("Subscribed Successfully!"))

    else:
      # Failed to create subscription
      return jsonify({'message': subscription_response.json()
                      }), subscription_response.status_code
  else:
    # Failed to obtain access token
    return redirect("https://jokepy.vercel.app/message?message=" +
                    quote("Unable To Obtain Access Token"))


@app.route('/delete')
def deleteSubscription():
  # Authenticate to get users tokens again
  client_id = os.environ.get('CLIENT_ID')
  redirect_uri = 'https://stravajokesv2.beelauuu.repl.co/delete_callback'
  scopes = 'activity:write,activity:read_all'
  authorization_url = f'https://www.strava.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}'
  return redirect(authorization_url)


@app.route('/delete_callback')
def deleteSubscriptionCallback():
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
  user_id = data['athlete']['id']
  existing_user = collection.find_one({'user_id': user_id})

  # Check if user is in the database
  if existing_user is not None:
    # Doing the deleting
    unsub_url = 'https://www.strava.com/oauth/deauthorize'
    params = {'access_token': data['access_token']}
    response = requests.post(unsub_url, data=params)
    collection.delete_one({'user_id': user_id})

    if response.status_code == 204 or response.status_code == 200:
      return redirect("https://jokepy.vercel.app/message?message=" +
                      quote("Deleted Successfully!"))

    else:
      return redirect("https://jokepy.vercel.app/message?message=" +
                      quote("Failed To Delete Subscription"))

  else:
    return redirect("https://jokepy.vercel.app/message?message=" +
                    quote("Failed To Delete Subscription"))


# Creates the endpoint for our webhook
@app.route('/webhook', methods=['POST'])
def webhook():
  print("Webhook event received!", request.args, request.json)
  if request.json['aspect_type'] == 'create' and request.json[
      'object_type'] == 'activity':
    joke.update_joke(request.json['owner_id'])
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
      print('Webhook has been verified!')
      return jsonify({'hub.challenge': challenge}), 200
    else:
      # Responds with '403 Forbidden' if verify tokens do not match
      return 'Forbidden', 403
  return 'Bad Request', 400


if __name__ == '__main__':
  app.run('0.0.0.0')
