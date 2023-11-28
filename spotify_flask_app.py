
from flask import Flask, request, redirect, jsonify
import random
import base64
import os
import string
import json
import requests
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Access environment variables
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

redirect_uri = 'http://localhost:3000/callback'

def generate_random_string(length):
    """
    Generates a random string of the specified length. 
    This function is typically used to create a unique 'state' parameter 
    during the OAuth 2.0 authorization process to prevent cross-site request forgery (CSRF) attacks.
    
    Parameters:
    - length (int): The length of the random string to generate.
    
    Returns:
    - str: A randomly generated string.
    """
    rand_Str = string.ascii_letters + string.digits
    return ''.join(random.choice(rand_Str) for _ in range(length))

@app.route('/login')
def login():
    state = generate_random_string(16)
    scope = 'user-read-private user-read-email user-read-recently-played playlist-read-private playlist-read-private user-top-read user-library-read user-follow-read'
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    }
    redirect_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode(params)
    return redirect(redirect_url)

@app.route('/callback')
def callback():
    code = request.args.get('code', None)
    state = request.args.get('state', None)

    if state is None:
        return jsonify({'error': 'state_mismatch'}), 400
    else:
        auth_options = {
            'url': 'https://accounts.spotify.com/api/token',
            'data': {
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            },
            'headers': {
                'content-type': 'application/x-www-form-urlencoded',
                'Authorization': 'Basic ' + base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8')
            }
        }

        response = requests.post(auth_options['url'], data=auth_options['data'], headers=auth_options['headers'])
        token_info = response.json()
        
        # Store the token_info for further analysis
        with open('token_info.json', 'w') as json_file:
            json_file.write(json.dumps(token_info, indent=4))
        
        # Return a response
        return jsonify({'message': 'Authentication successful'})

@app.route('/refresh_token')
def refresh_token():
    refresh_token = request.args.get('refresh_token', None)

    if refresh_token is None:
        return jsonify({'error': 'missing_refresh_token'}), 400

    auth_options = {
        'url': 'https://accounts.spotify.com/api/token',
        'data': {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        },
        'headers': {
            'content-type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8')
        }
    }

    response = requests.post(auth_options['url'], data=auth_options['data'], headers=auth_options['headers'])
    token_info = response.json()
    # Write the modified token_info back to the file
    with open('token_info_refreshed.json', 'w') as json_file:
        json.dump(token_info, json_file, indent=4)
        
    # Load existing token_info from the file
    with open('token_info.json', 'r') as json_file:
        token_info = json.load(json_file)

    # Load refreshed token_info from the file
    with open('token_info_refreshed.json', 'r') as refreshed_json_file:
        refreshed_token_info = json.load(refreshed_json_file)

    # Update the original token_info with the refreshed access_token
    token_info['access_token'] = refreshed_token_info['access_token']

    # Write the modified token_info back to the file
    with open('token_info.json', 'w') as json_file:
        json.dump(token_info, json_file, indent=4)
        
    return jsonify({'message': 'Token have been successfully refreshed'})

if __name__ == '__main__':
    app.run(port=3000)