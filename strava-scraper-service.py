from flask import Flask, request
import webbrowser
import threading
import requests
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:5000/"
SCOPE = 'activity:read_all'

app = Flask(__name__)

@app.route('/')
def home():
    code = request.args.get('code')
    try:
        print(f"Authorization Code: {code}")
        token = fetch_token(code)
        ids = fetch_activity_ids(token)
        activities = fetch_activities(ids, token)
        activities_df = pd.DataFrame(activities)
        activities_df.set_index("id")
        activities_df.to_csv("activities.csv")
    except Exception:
        return "failed"

    return "finished scraping!"

def fetch_token(code):
    url = f"https://www.strava.com/oauth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&code={code}&grant_type=authorization_code"
    r = requests.post(url)
    token = ""
    if r.status_code != 200:
        print("Failed to fetch token: ", r.text)
        raise Exception()
    
    token = r.json()["access_token"]
    print(f"Access token: {token}")        

    return token

def fetch_activity_ids(token):
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    header = {'Authorization': 'Bearer ' + token}
    page = 1 # Update accordingly depending on the last page pulled.
    per_page = 50
    activity_ids = []
    count = 0
    while count < 1: # Pull only 50 at a time (max 100 requests every 15 minutes and we need the other 50 to fetch the detailed activities).
        params = {"per_page": per_page, "page": page}
        r = requests.get(activites_url, headers=header, params=params)
        if r.status_code != 200:
            print("Failed to fetch activity IDs: ", r.text)
            raise Exception()
        if not r:
            break
        for activity in r.json():
            activity_ids.append(activity["id"])
        print(f"Last page pulled: {page}")
        page += 1
        count += 1

    print(f"# of Activity IDs Extracted: {len(activity_ids)}")
    return activity_ids

def fetch_activities(ids, token):
    header = {'Authorization': 'Bearer ' + token}
    activities = []
    for i in range(len(ids)):
        detailed_activites_url = f"https://www.strava.com/api/v3/activities/{ids[i]}?include_all_efforts=true"
        r = requests.get(detailed_activites_url, headers=header)

        if r.status_code != 200:
            print("Failed to fetch detailed activities: ", r.text)
            print(f"Failed activity ids: {ids[i:]}")
            raise Exception()
        
        activities.append(r.json())

    print(f"# of Detailed Activities Extracted: {len(activities)}")
    return activities

def fetch_activity(id, header):
    detailed_activites_url = f"https://www.strava.com/api/v3/activities/{id}?include_all_efforts=true"
    r = requests.get(detailed_activites_url, headers=header)

    if r.status_code != 200:
        print("Failed to fetch detailed activities: ", r.text)
        raise Exception()
    
    return r.json()

def fetch_code():
    auth_url = f'https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPE}'
    webbrowser.open(auth_url)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=app.run, kwargs={'port': 5000})
    flask_thread.start()
    fetch_code()
    flask_thread.join()
