from enum import Enum
import os

from urllib import parse

from googleapiclient.discovery import build

from settings import *

# initialize youtube http api client
youtube = build("youtube", "v3" , developerKey=YOUTUBE_TOKEN)

class YoutubeUrlType(Enum):
  PLAYLIST = 1,
  VIDEO = 2,
  OTHER = 3

def get_params_from_url(url):
  return dict(parse.parse_qsl(parse.urlsplit(url).query))

def get_url_type(url):
  params = get_params_from_url(url)

  if params.get('list') != None: 
    return YoutubeUrlType.PLAYLIST
  elif params.get('v') != None: 
    return YoutubeUrlType.VIDEO
  else: 
    return YoutubeUrlType.OTHER

def get_videos_snippet_from_playlist_id(playlist_id):
  videos_snippets = []

  request = youtube.playlistItems().list(part='snippet', maxResults=50, playlistId=playlist_id)
  response = request.execute()

  for item in response['items']:
    videos_snippets.append(item["snippet"])

  return videos_snippets

def get_videos_ids_from_playlist_id(playlist_id):
  videos_ids = []

  for item in get_videos_snippet_from_playlist_id(playlist_id):
      videos_ids.append(item['resourceId']['videoId'])

  return videos_ids

def get_videos_snippet_from_playlist_url(url):
  params = get_params_from_url(url)
  playlist_id = params["list"]
  return get_videos_snippet_from_playlist_id(playlist_id)

def get_video_snippet_from_video_id(video_id):
  request = youtube.videos().list(part="id,snippet", id=video_id)
  response = request.execute()

  return response["items"][0]["snippet"]

def get_video_snippet_from_video_url(url):
  video_id = get_video_id_from_video_url(url)
  return get_video_snippet_from_video_id(video_id)

def get_videos_ids_from_playlist_url(url):
  params = get_params_from_url(url)
  playlist_id = params["list"]
  return get_videos_ids_from_playlist_id(playlist_id)

def get_video_id_from_video_url(url):
  params = get_params_from_url(url)
  video_id = params["v"]
  return video_id

# returns an array of videos snippets contained in the specified resource of the provided url
def get_videos_snippet_from_url(url):
  url_type = get_url_type(url)

  if(url_type == YoutubeUrlType.PLAYLIST):
    return get_videos_snippet_from_playlist_url(url)

  elif (url_type == YoutubeUrlType.VIDEO):
    return [get_video_snippet_from_video_url(url)]

  return None

# the info object is a dicttionary containting: {video_id : "...", video_title : "..."}
def get_videos_info_from_url(url):
  url_type = get_url_type(url)

  videos_info = []

  if(url_type == YoutubeUrlType.PLAYLIST):
    snippets =  get_videos_snippet_from_playlist_url(url)

    for snippet in snippets:
      videos_info.append({
        "video_id" : snippet["resourceId"]["videoId"],
        "video_title" : snippet["title"]
      })

  elif (url_type == YoutubeUrlType.VIDEO):
    video_id = get_video_id_from_video_url(url);
    snippet = get_video_snippet_from_video_id(video_id)
    
    videos_info.append({
      "video_id" : video_id,
      "video_title" : snippet["title"]
    })

  return videos_info

# returns an array of videos_ids contained in the specified resource of the provided url
def get_videos_ids_from_url(url):
  url_type = get_url_type(url)

  if(url_type == YoutubeUrlType.PLAYLIST):
    return get_videos_ids_from_playlist_url(url)

  elif (url_type == YoutubeUrlType.VIDEO):
    return [get_video_id_from_video_url(url)]

  return None

def get_videos_urls_from_url(url):
  videos_urls = []

  videos_ids = get_videos_ids_from_url(url)

  for id in videos_ids:
    videos_urls.append(f"https://www.youtube.com/watch?v={id}")

  return videos_urls

def get_video_seach(query="", inclusions=[], exclusions=[], _order="rating", _safeSearch="none", _type="video", _videoDuration="any", _videoCategoryId="10", _maxResults=45): # videoCategoryId 10 is for music
  #pre process the query, pending...

  #add the inclusions to query
  for inclusion in inclusions:
    query += f" |{inclusion} "

  #add exclusions to query
  for exclusion in exclusions:
    query += f" -{exclusion} "

  request = youtube.search().list(part="snippet", q=query, order=_order, safeSearch=_safeSearch, type=_type, videoCategoryId=_videoCategoryId, videoDuration=_videoDuration, maxResults=_maxResults)
  response = request.execute()

  return response["items"]

def get_videos_search_from_query(query):
  response = get_video_seach(query)

  return response

# returns the first result video_id for the given query
def get_video_id_from_search(query):
  searches = get_videos_search_from_query(query)

  if searches:
    return searches[0]["id"]["videoId"]

if __name__ == "__main__":

  video_id = "4eqEc-qV89s"
  video_url = "https://www.youtube.com/watch?v=H9PcF5VrYpM&ab_channel=CumbiaNinjaUruguay"

  # print(get_video_snippet_from_id(video_id))
  # print(get_videos_ids_from_url(video_url))
  # print(get_video_id_from_video_url(video_url))
  print(get_video_snippet_from_video_id(video_id)["title"])