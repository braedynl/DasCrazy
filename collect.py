import re
from datetime import datetime
from socket import socket
from typing import Tuple

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


def fetch_metadata() -> Tuple[str, str]:
    try:
        resp = requests.get(REQUEST_URL, headers=REQUEST_HEADERS).json()
        data = resp['data'][0]
        return data['game_name'], data['title']

    except Exception as e:
        print(f"Exception occured while fetching metadata: {e}")

    return 'UNKNOWN', 'UNKNOWN'


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
                    game_name, title = fetch_metadata()

                    row_template["sent"] = sent
                    row_template["game_name"] = game_name
                    row_template["title"] = title
                    row_template["user"] = user
                    row_template["message"] = message

                    df = df.append(row_template, ignore_index=True)
                    print(f"[{sent}] {message}")

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
