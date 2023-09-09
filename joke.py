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

def update_joke(user_id):
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
  if ('🤡 Joke Of The Activity 🤡' not in current_description):
    random_number = random.randint(1, 5)
    # Joke API #1
    if random_number == 1:
      limit = 1
      api_url = 'https://api.api-ninjas.com/v1/jokes?limit={}'.format(limit)
      response = requests.get(api_url, headers={'X-Api-Key': 'FGlq+GeY3I6j8GCVQggQlw==y8452egm19j1CPOL'})
      data = response.json()
      headers = {'Authorization': 'Bearer ' + access_token}
      updatableActivity = {
          'description':
          '🤡 Joke Of The Activity 🤡\n' + data[0]['joke'] + '\n- by Joke.py (v2)' +
          '\n\n' + current_description
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
          '🤡 Joke Of The Activity 🤡\n' + data["joke"] + '\n- by Joke.py (v2)' +
          '\n\n' + current_description
        }
        response = requests.put(url + '/activities/' + str(activity_id),
                                headers=headers,
                                json=updatableActivity)
    #Joke API #3
    elif random_number == 3:
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
        '🤡 Joke Of The Activity 🤡\n' + joke["body"][0]["setup"] + '\n' +
        joke["body"][0]["punchline"] + '\n- by Joke.py (v2)' + '\n\n' +
        current_description
      }
      response = requests.put(url + '/activities/' + str(activity_id),
                              headers=headers,
                              json=updatableActivity)
    # Joke API #4
    elif random_number == 4:
      url = 'https://backend-omega-seven.vercel.app/api/getjoke'
      response = requests.get(url)
      joke = response.json()
      headers = {'Authorization': 'Bearer ' + access_token}
      updatableActivity = {
        'description':
        '🤡 Joke Of The Activity 🤡\n' + joke[0]['question'] + '\n' +
        joke[0]['punchline'] + '\n- by Joke.py (v2)' + '\n\n' +
        current_description
      }
      response = requests.put(url + '/activities/' + str(activity_id),
                              headers=headers,
                              json=updatableActivity)
    # Joke API #5
    else:
      url = 'https://official-joke-api.appspot.com/random_joke'
      response = requests.get(url)
      joke = response.json()
      headers = {'Authorization': 'Bearer ' + access_token}
      updatableActivity = {
        'description':
        '🤡 Joke Of The Activity 🤡\n' + joke['setup'] + '\n' +
        joke['punchline'] + '\n- by Joke.py (v2)' + '\n\n' +
        current_description
      }
      response = requests.put(url + '/activities/' + str(activity_id),
                              headers=headers,
                              json=updatableActivity)

# For testing purposes
# update_joke(41098360)
