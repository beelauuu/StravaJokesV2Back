import requests
from dotenv import load_dotenv
import os
from jokeapi import Jokes
from pymongo import MongoClient
import asyncio

auth_url = 'https://www.strava.com/api/v3/oauth/token'
url = 'https://www.strava.com/api/v3'
load_dotenv()
client = MongoClient(
  'mongodb+srv://blau1:SwPJFDVOvQ8aLAUm@cluster0.ziyuaoy.mongodb.net/?retryWrites=true&w=majority'
)
db = client['StravaJokes']
collection = db['users']

async def update_joke(user_id):
  #Get the users tokens, if they exist   
  user = collection.find_one({'user_id': user_id})
  if user is None:
    return 'FAILED'
  
  #Retrieving refresh token
  payload = {
    'client_id': os.environ.get('CLIENT_ID'),
    'client_secret': os.environ.get('CLIENT_SECRET'),
    'grant_type': 'refresh_token',
    'refresh_token': user['refresh_token']
  }
  response = requests.post(
    auth_url,
    data=payload,
  )
  access_token = response.json()['access_token']

  #Getting first (most recent) activity id
  headers = {'Authorization': 'Bearer ' + access_token}
  param = {'page': 1, 'per_page': 1}
  response = requests.get(url + '/athlete/activities',
                          headers=headers,
                          params=param)
  activity_id = response.json()[0]['id']

  #Get current description
  headers = {'Authorization': 'Bearer ' + access_token}
  response = requests.get(
    url + '/activities/' + str(activity_id),
    headers=headers,
  )
  current_description = response.json()['description']
  if current_description is None:
    current_description = ''

  #Updating activity description
  if ('🤡 Joke of the day 🤡' not in current_description):
    j = await Jokes()  # Initialise the class
    joke = await j.get_joke(blacklist=['explicit','sexist', 'racist'])  # Retrieve a random joke
    
    # One-liner joke
    if joke["type"] == "single":
      headers = {'Authorization': 'Bearer ' + access_token}
      updatableActivity = {
        'description':
        '🤡 Joke of the day 🤡\n' + joke["joke"] + '\n- by Joke.py v2' + '\n\n' +
        current_description
      }
      response = requests.put(url + '/activities/' + str(activity_id),
                              headers=headers,
                              params=updatableActivity)
    # Two-part joke
    else:
      headers = {'Authorization': 'Bearer ' + access_token}
      updatableActivity = {
        'description':
        '🤡 Joke of the day 🤡\n' + joke["setup"] + '\n' + joke["delivery"] +
        '\n- by Joke.py (v2)' + '\n\n' + current_description
      }
      response = requests.put(url + '/activities/' + str(activity_id),
                              headers=headers,
                              params=updatableActivity)
