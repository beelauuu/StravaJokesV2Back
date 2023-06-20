import requests
from dotenv import load_dotenv
import os
from jokeapi import Jokes
from pymongo import MongoClient
import random
import asyncio

auth_url = 'https://www.strava.com/api/v3/oauth/token'
load_dotenv()
client = MongoClient(
  f'mongodb+srv://{os.environ.get("DB_USERNAME")}:{os.environ.get("DB_PASSWORD")}@cluster0.ziyuaoy.mongodb.net/?retryWrites=true&w=majority'
)
db = client['StravaJokes']
collection = db['users']


async def update_joke(user_id):
  url = 'https://www.strava.com/api/v3'
  user = collection.find_one({'user_id': user_id})
  if user is None:
    print('User is not found!')
    return
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
    random_number = random.randint(1, 3)
    # Joke API #1
    if random_number == 1:
      j = await Jokes()
      joke = await j.get_joke(blacklist=['sexist', 'racist', 'explicit'])
      # One-liner joke
      if joke["type"] == "single":
        headers = {'Authorization': 'Bearer ' + access_token}
        updatableActivity = {
          'description':
          '🤡 Joke of the day 🤡\n' + joke["joke"] + '\n- by Joke.py (v2)' +
          '\n\n' + current_description
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
    #Joke API #2
    elif random_number == 2:
      url_two = "https://icanhazdadjoke.com/"
      headers = {"Accept": "application/json"}
      response = requests.get(url_two, headers=headers)
      if response.status_code == 200:
        data = response.json()
        headers = {'Authorization': 'Bearer ' + access_token}
        updatableActivity = {
          'description':
          '🤡 Joke of the day 🤡\n' + data["joke"] + '\n- by Joke.py (v2)' +
          '\n\n' + current_description
        }
        response = requests.put(url + '/activities/' + str(activity_id),
                                headers=headers,
                                params=updatableActivity)
    #Joke API #3
    else:
      url_three = "https://dad-jokes.p.rapidapi.com/random/joke"
      headers = {
        "X-RapidAPI-Key": "9f3d93e966mshd0b57f74285ca1fp1e8cdfjsnaa1b553880fa",
        "X-RapidAPI-Host": "dad-jokes.p.rapidapi.com"
      }
      response = requests.get(url_three, headers=headers)
      joke = response.json()
      headers = {'Authorization': 'Bearer ' + access_token}
      updatableActivity = {
        'description':
        '🤡 Joke of the day 🤡\n' + joke["body"][0]["setup"] + '\n' + joke["body"][0]["punchline"] +
        '\n- by Joke.py (v2)' + '\n\n' + current_description
      }
      response = requests.put(url + '/activities/' + str(activity_id),
                              headers=headers,
                              params=updatableActivity)
      
