import re
import time
from datetime import datetime
from socket import socket
from threading import Thread

import pandas as pd
import requests

from keys import BEARER_TOKEN, CLIENT_ID, IRC_TOKEN

# User information
PERSONAL_LOGIN = "braedynl_"
BROADCASTER_LOGIN = "hasanabi"
BROADCASTER_ID = 207813352

# API stuff
SERVER = "irc.chat.twitch.tv"
PORT = 6667
REQUEST_URL = f"https://api.twitch.tv/helix/channels?broadcaster_id={BROADCASTER_ID}"
REQUEST_HEADERS = {"Client-Id": CLIENT_ID, "Authorization": f"Bearer {BEARER_TOKEN}"}

# IRC response pattern
SEARCH_PATTERN = re.compile(f":(.*)!.* PRIVMSG #{BROADCASTER_LOGIN} :(.*)\r\n")

# Global variables (cheesy, I know)
game_name = ''
title = ''


def metadata_worker() -> None:
    global game_name, title

    while True:
        resp = requests.get(REQUEST_URL, headers=REQUEST_HEADERS).json()
        data = resp['data'][0]
        game_name = data['game_name']
        title = data['title']

        print(f"[{datetime.now()}] Metadata updated")
        time.sleep(900)


def main(filename: str) -> None:
    sock = socket()
    sock.connect((SERVER, PORT))

    sock.send(f"PASS oauth:{IRC_TOKEN}\n".encode("utf-8"))
    sock.send(f"NICK {PERSONAL_LOGIN}\n".encode("utf-8"))
    sock.send(f"JOIN #{BROADCASTER_LOGIN}\n".encode("utf-8"))

    resp = sock.recv(2048).decode("utf-8", errors='ignore')

    if not resp.startswith(f":tmi.twitch.tv 001 {PERSONAL_LOGIN} :Welcome, GLHF!"):
        resp = resp.replace('\n', '').replace('\r', '')
        raise RuntimeError(f"Connection to Twitch IRC failed, response: {resp}")

    print("Connection to Twitch IRC successful, entering main loop...")
    print("Use CTRL + C to stop at anytime\n--")

    # Creates a thread to fetch stream metadata every 15 minutes, since it doesn't
    # change often and the main loop needs to be fast
    t = Thread(target=metadata_worker, daemon=True)
    t.start()

    df = pd.read_csv(f'data/{filename}.csv')
    row_template = {"sent": '', "game_name": '', "title": '', "user": '', "message": ''}

    try:
        while True:
            resp = sock.recv(2048).decode("utf-8", errors='ignore')

            if resp.startswith("PING"):
                sock.send("PONG\n".encode("utf-8"))
                print(f"[{datetime.now()}] PING")
                continue

            groups = SEARCH_PATTERN.findall(resp)

            for user, message in groups:

                if "peepoHas" in message:
                    sent = datetime.now()

                    # Declaring a dictionary and setting its values later is faster than
                    # creating a dictionary with initial values - fun fact!
                    row_template["sent"] = sent
                    row_template["game_name"] = game_name
                    row_template["title"] = title
                    row_template["user"] = user
                    row_template["message"] = message

                    df = df.append(row_template, ignore_index=True)
                    print(f"[{sent}] {user}: {message}")

    except Exception as e:
        print(f"Exception occurred in main loop: {e}")

    except KeyboardInterrupt:
        pass

    print("Closing socket and exporting data...")

    sock.close()
    df.to_csv(f'data/{filename}.csv', index=False)

    print("Done.")


if __name__ == "__main__":
    main('data')
