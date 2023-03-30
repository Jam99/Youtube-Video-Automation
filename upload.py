#!/usr/bin/python


import argparse
import http.client
import httplib2
import os
import random
import time
import json
import glob
import re

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

from io import StringIO
from html.parser import HTMLParser


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = 'client_secret.json'

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')


# Authorize the request and store authorization credentials.
def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  #credentials = flow.run_console()
  credentials = flow.run_local_server()
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def initialize_upload(youtube, options):
  body=dict(
    snippet=dict(
      title=options["title"],
      description=options["description"],
      tags=options["tags"],
      categoryId=options["category"]
    ),
    status=dict(
      privacyStatus=options["privacyStatus"],
      selfDeclaredMadeForKids=options["selfDeclaredMadeForKids"]
    )
  )

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=','.join(list(body.keys())),
    body=body,
    # The chunksize parameter specifies the size of each chunk of data, in
    # bytes, that will be uploaded at a time. Set a higher value for
    # reliable connections as fewer chunks lead to faster uploads. Set a lower
    # value for better recovery on less reliable connections.
    #
    # Setting 'chunksize' equal to -1 in the code below means that the entire
    # file will be uploaded in a single HTTP request. (If the upload fails,
    # it will still be retried where it left off.) This is usually a best
    # practice, but if you're using Python older than 2.6 or if you're
    # running on App Engine, you should set the chunksize to something like
    # 1024 * 1024 (1 megabyte).
    media_body=MediaFileUpload(options["file"], chunksize=-1, resumable=True)
  )
  return resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print('Uploading file...')
      status, response = request.next_chunk()
      if response is not None:
        if 'id' in response:
          print('Video id "%s" was successfully uploaded.' % response['id'])
          return response["id"]
        else:
          exit('The upload failed with an unexpected response: %s' % response)
    except HttpError as e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS as e:
      error = 'A retriable error occurred: %s' % e

    if error is not None:
      print(error)
      retry += 1
      if retry > MAX_RETRIES:
        exit('No longer attempting to retry.')

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print('Sleeping %f seconds and then retrying...' % sleep_seconds)
      time.sleep(sleep_seconds)


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


if __name__ == '__main__':
  youtube = get_authenticated_service()

  video_file_paths = glob.glob("output/*.mp4")

  if(len(video_file_paths) == 0):
    exit("There is nothing to upload.")

  #shuffle list to avoid boring upload sequence
  random.shuffle(video_file_paths)

  if(len(video_file_paths) > 5):
    tmp_ending_index = 6
  else:
    tmp_ending_index = len(video_file_paths)

  #subset to reduce the list as youtube API quota will not allow more than 6 videos
  video_file_paths = video_file_paths[0:tmp_ending_index]

  print("The following video(s) will be uploaded ("+ str(len(video_file_paths)) +")):")
  for video_file_path in video_file_paths:
    print(video_file_path)

  success_count = 0

  for video_file_path in video_file_paths:
    try:
      re_result = re.search('^output\\\(.+) vs (.+)\.mp4$', video_file_path)
      title_a = re_result.group(1)
      title_b = re_result.group(2)

      id = initialize_upload(youtube, {
          "file": video_file_path,
          "title": title_a +" vs "+ title_b,
          "description": title_a +" versus "+ title_b +" #shorts #viral #trending #comparison",
          "category": "24",
          "tags": [title_a, title_b, "Versus", "Comparison"],
          "privacyStatus": "public",
          "selfDeclaredMadeForKids": False
      })

      if(id is not None):
        os.replace(video_file_path, video_file_path.replace("output\\", "output_uploaded\\"))
        success_count += 1


    except HttpError as e:
      print('An HTTP error %d occurred:\n%s' % (e.resp.status, strip_tags(json.loads(e.content)["error"]["message"])))

  print(str(success_count) +" videos were uploaded.")