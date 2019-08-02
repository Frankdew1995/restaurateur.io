import os




access_token="ya29.GltDB-13YHBdwqxyQqjJ7zrlcf-NZlDh6rZ8I1gTm7qi8jzlyp3KzWjSfPBWqmU_3kPjRRl-EK-8d2p3KyG4oAUcd6XN8KzbCPBjdVAFy2YwqtsUJOOK-hQJXfwV"

CLIENT_ID = '24098347452-uojtb9hqnk2v9r5ueeo0f885lafo610u.apps.googleusercontent.com'
CLIENT_SECRET = 'zVShfIvGSTY0se41gtAUHWp8'



print(os.environ)


import time
import requests


class CloudPrint():

    def __init__(self, client_id,
                 client_secret,
                 access_token,
                 refresh_token=None):

            self.client_id = client_id
            self.client_secret= client_secret
            self.access_token = access_token
            self.refresh_token = refresh_token
            self.deadline = time.time()-1
            self.api_url ='https://www.google.com/cloudprint/submit'

    def print_file(self, file, title, printerids):


        ticket = {
                 "version": "1.0",
                 "print": {
                  "color": {
                    "type": "STANDARD_COLOR",
                  },
                  "duplex": {
                    "type": "NO_DUPLEX"
                  },
                  "copies": {"copies": 1},
                  "media_size": {
                     "width_microns": 27940,
                     "height_microns": 60960
                  },
                  "page_orientation": {
                    "type": "LANDSCAPE"
                  },
                   "margins": {
                     "top_microns": 0,
                     "bottom_microns": 0,
                     "left_microns": 0,
                     "right_microns": 0
                  },
                  "page_range": {
                      "interval": [
                        {
                          "start": 1,
                          "end": 2
                        },

                      ]
                    }
                 }
                }

        body = {"printerid": printerids,
                "title": [title],
                "ticket": "",
                }


        files = {'content': file}

        headers = {"Authorization": "Bearer " + str(self.access_token)}
        print(headers)
        r = requests.post(self.api_url, data=body, files=files, headers=headers)
        print(r.url)
        print(r.text)

    def print_printerinfo(self, printerid):


        url = "https://www.google.com/cloudprint/printer"


        body = {"printerid": printerid}

        headers = {"Authorization": "Bearer " + str(self.access_token)}
        print(headers)
        r = requests.post(url, data=body, headers=headers)
        print(r.url)
        print(r.text)




# cloudprint = CloudPrint(access_token=access_token,
#                         client_id=CLIENT_ID,
#                         client_secret=CLIENT_SECRET)
#
#
# cloudprint.print_printerinfo(printerid="728a4680-689b-bee6-5730-cd577d6f163c")


