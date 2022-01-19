import sys
import json
import urllib.parse
from pathlib import Path

import requests
import ffmpeg


# References:
#  - https://note.com/kohnoselami/n/nb8ef0eea5831
#  - https://gist.github.com/osakanataro/5ee1b6dfa3d1f12f8c2b4492b1676aa8


def getGuest(bearer):
    guestActivate = 'https://api.twitter.com/1.1/guest/activate.json'

    res = requests.post(guestActivate, headers={
                        'Authorization': 'Bearer ' + bearer})

    return res.json()['guest_token']


def getAudioSpaceGraphQl(bearer, g_token, space_id):
    url = 'https://twitter.com/i/api/graphql/FJoTSHMVF7fMhGLc2t9cog/AudioSpaceById'

    variables = {
        "id": space_id,
        "isMetatagsQuery": False,
        "withSuperFollowsUserFields": False,
        "withUserResults": True,
        "withBirdwatchPivots": False,
        "withReactionsMetadata": False,
        "withReactionsPerspective": False,
        "withSuperFollowsTweetFields": False,
        "withScheduledSpaces": True
    }

    res = requests.get(url + '?variables=' + urllib.parse.quote(json.dumps(variables)), headers={
        'Authorization': 'Bearer ' + bearer,
        'X-Guest-Token': g_token})

    return res.json()


def getStreamInfo(bearer, g_token, media_id):
    url = 'https://twitter.com/i/api/1.1/live_video_stream/status/' + media_id + \
        '?client=web&use_syndication_guest_id=false&cookie_set_host=twitter.com'

    res = requests.get(url, headers={
        'Authorization': 'Bearer ' + bearer,
        'X-Guest-Token': g_token})

    return res.json()


def getStreamingUrl(space_id):
    bearer = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'

    g_token = getGuest(bearer)
    asGraphQl = getAudioSpaceGraphQl(bearer, g_token, space_id)

    metadata = asGraphQl['data']['audioSpace']['metadata']

    space_media_key = metadata['media_key']

    admins = asGraphQl['data']['audioSpace']['participants']['admins']

    streamInfo = getStreamInfo(bearer, g_token, space_media_key)

    streaming_url = streamInfo['source']['location']

    return metadata, admins, streaming_url


def recordAudio(stream_url, filename):
    i = ffmpeg.input(stream_url)
    cmd = i.output(filename)
    cmd.run()


if (len(sys.argv) != 2):
    print('Usage: ./main.py <space_id>')
    exit(1)

metadata, admins, streaming_url = getStreamingUrl(sys.argv[1])

space_id = metadata['rest_id']
space_title = metadata['title']
#space_state = metadata['state']

first_admin = admins[0]

dirname = 'records/' + first_admin['user']['rest_id'] + \
    '_' + first_admin['twitter_screen_name']

filename = space_title + '_' + space_id + '.aac'


Path(dirname).mkdir(parents=True, exist_ok=True)

# print(streaming_url)

recordAudio(streaming_url, dirname + '/' + filename)
