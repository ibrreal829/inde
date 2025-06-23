import os

import time

import json

import urllib.request

import urllib.parse

import subprocess



TOKEN = '7850703374:AAEBF-vJwHcn6bflQCEr4pTBkvuAtubftwI'

API_URL = f'https://api.telegram.org/bot{TOKEN}'



DOWNLOAD_DIR = 'downloads'

if not os.path.exists(DOWNLOAD_DIR):

    os.makedirs(DOWNLOAD_DIR)



YTDLP_BIN = './yt-dlp'  # Adjust if yt-dlp is elsewhere



def get_updates(offset=None):

    url = f"{API_URL}/getUpdates?timeout=100"

    if offset:

        url += f"&offset={offset}"

    with urllib.request.urlopen(url) as response:

        return json.load(response)



def send_message(chat_id, text):

    data = urllib.parse.urlencode({'chat_id': chat_id, 'text': text}).encode()

    req = urllib.request.Request(f"{API_URL}/sendMessage", data=data)

    urllib.request.urlopen(req)



def send_video(chat_id, video_path):

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

    data = []

    data.append(f'--{boundary}')

    data.append('Content-Disposition: form-data; name="chat_id"\r\n')

    data.append(str(chat_id))

    data.append(f'--{boundary}')

    data.append(f'Content-Disposition: form-data; name="video"; filename="{os.path.basename(video_path)}"')

    data.append('Content-Type: video/mp4\r\n')



    with open(video_path, 'rb') as f:

        video_data = f.read()



    body_pre = '\r\n'.join(data).encode() + b'\r\n'

    body_post = f'\r\n--{boundary}--\r\n'.encode()



    body = body_pre + video_data + body_post



    headers = {

        'Content-Type': f'multipart/form-data; boundary={boundary}',

        'Content-Length': str(len(body))

    }



    req = urllib.request.Request(f"{API_URL}/sendVideo", data=body, headers=headers)

    urllib.request.urlopen(req)



def download_video(url):

    # Use yt-dlp to download best mp4 progressive format video

    cmd = [

        YTDLP_BIN,

        '-f', 'best[ext=mp4]/best',

        '-o', os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),

        url

    ]

    proc = subprocess.run(cmd, capture_output=True)

    if proc.returncode != 0:

        raise Exception(proc.stderr.decode())



    # Return newest file in download dir

    files = sorted(

        [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)],

        key=os.path.getmtime,

        reverse=True

    )

    if not files:

        raise Exception("No video downloaded")

    return files[0]



def main():

    print("Bot started, polling...")

    offset = None

    while True:

        try:

            updates = get_updates(offset)

            for update in updates.get('result', []):

                offset = update['update_id'] + 1

                message = update.get('message')

                if not message:

                    continue

                chat_id = message['chat']['id']

                text = message.get('text', '')



                if text.startswith('/start'):

                    send_message(chat_id, "Send me a YouTube video URL, I'll download it for you!")

                    continue



                if 'youtube.com' in text or 'youtu.be' in text:

                    send_message(chat_id, "Downloading video, please wait...")

                    try:

                        video_path = download_video(text)

                        send_video(chat_id, video_path)

                        send_message(chat_id, "Done! Here's your video.")

                        os.remove(video_path)

                    except Exception as e:

                        send_message(chat_id, f"Error: {e}")

                else:

                    send_message(chat_id, "Please send a valid YouTube URL.")

        except Exception as e:

            print("Error:", e)

            time.sleep(5)

        time.sleep(1)



if __name__ == '__main__':

    main()
