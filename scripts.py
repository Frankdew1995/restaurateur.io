
# from app.models import User, Visit, Order, Food
# from app import app, db




# import json
# import pendulum as pen
# from functools import reduce




# from pathlib import Path
# import pandas as pd
#
# import pyqrcode
#
'''
    This script will attempt to open your webbrowser,
    perform OAuth 2 authentication and print your access token.
    It depends on two libraries: oauth2client and gflags.
    To install dependencies from PyPI:
    $ pip install python-gflags oauth2client
    Then run this script:
    $ python get_oauth2_token.py

    This is a combination of snippets from:
    https://developers.google.com/api-client-library/python/guide/aaa_oauth
'''

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run_flow
from oauth2client.file import Storage

CLIENT_ID = '24098347452-uojtb9hqnk2v9r5ueeo0f885lafo610u.apps.googleusercontent.com'
CLIENT_SECRET = 'zVShfIvGSTY0se41gtAUHWp8'

access_token = "ya29.GltDB6dqdPNjUzlnfWiSknjnJRjIX9LzGC0cKFCjKohmHmyoPsj63VgxYOUbyOGCZ8jENzncDWXq2v8V_-0hX515s32kzo6IWs8Jo5NbPOWKhmgTWsI_86irz9Qs"


flow = OAuth2WebServerFlow(client_id=CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           scope='https://www.googleapis.com/auth/cloudprint https://www.googleapis.com/auth/drive.metadata.readonly',
                           redirect_uri='http://localhost:8080/')


storage = Storage('creds.data')

credentials = run_flow(flow, storage)

print("access_token: %s" % credentials.access_token)



