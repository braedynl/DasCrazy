import re
import sys
import time
import warnings
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


def irc_connect() -> socket:

    for timeout in (2, 4, 8, 16, -1):
        sock = socket()
        sock.connect((SERVER, PORT))

        sock.send(f"PASS oauth:{IRC_TOKEN}\n".encode("utf-8"))
        sock.send(f"NICK {PERSONAL_LOGIN}\n".encode("utf-8"))
        sock.send(f"JOIN #{BROADCASTER_LOGIN}\n".encode("utf-8"))

        resp = sock.recv(1024).decode("utf-8", errors='ignore')

        if resp.startswith(f":tmi.twitch.tv 001 {PERSONAL_LOGIN} :Welcome, GLHF!"):
            print(f"[{datetime.now()}] Connection to Twitch IRC successful, entering main loop...")
            print(f"[{datetime.now()}] Use CTRL + C to stop at anytime\n--")
            return sock

        print(f"[{datetime.now()}] Twitch IRC login failed, attempting restart...")
        sock.close()

        if timeout == -1:
            raise RuntimeError(f"[{datetime.now()}] Could not connect to Twitch IRC")

        time.sleep(timeout)


def fetch_metadata() -> Tuple[str, str]:
    resp = requests.get(REQUEST_URL, headers=REQUEST_HEADERS)

    if resp.status_code == 200:
        metadata = resp.json()['data'][0]
        return metadata['game_name'], metadata['title']

    warnings.warn(f"Metadata fetch request unsuccessful, response: {resp}")
    return '', ''


def collect(filename: str, start: str, stop: str, format: str = "%m/%d/%Y %I:%M %p %z", refresh_every: float = 15) -> None:

    def collect_helper(delta: float) -> bool:
        sock = irc_connect()
        game_name, title = fetch_metadata()

        df = pd.read_csv(f'data/{filename}.csv')
        row_template = {"sent": '', "game_name": '', "title": '', "user": '', "message": ''}

        errstate = False
        time_end = time.time() + delta

        try:
            while time.time() < time_end:
                resp = sock.recv(2048).decode("utf-8", errors='ignore')

                # Using stdout.write instead of print because it's sliiiightly faster
                # sys.stdout.write(resp)

                if resp.startswith("PING"):
                    sock.send("PONG\n".encode("utf-8"))
                    sys.stdout.write(f"[{datetime.now()}] PING\n")
                    continue

                groups = SEARCH_PATTERN.findall(resp)

                for user, message in groups:

                    if "peepoHas" in message:
                        sent = datetime.now()

                        # Declaring a dictionary and setting its values later is faster than
                        # creating a dictionary with initial values
                        row_template["sent"] = sent
                        row_template["game_name"] = game_name
                        row_template["title"] = title
                        row_template["user"] = user
                        row_template["message"] = message

                        df = df.append(row_template, ignore_index=True)
                        sys.stdout.write(f"[{sent}] {user}: {message}\n")

        except KeyboardInterrupt:
            errstate = True

        print(f"[{datetime.now()}] Closing socket and exporting data...")

        sock.close()
        df.to_csv(f'data/{filename}.csv', index=False)

        print(f"[{datetime.now()}] Done.")

        return errstate

    if start is not None:
        sleep_time = datetime.strptime(start, format).timestamp() - time.time()
        print(f"[{datetime.now()}] Starting collection in {sleep_time} seconds...")
        time.sleep(sleep_time)

    ts_end = datetime.strptime(stop, format).timestamp()

    while time.time() < ts_end:
        if collect_helper(delta=refresh_every * 60):
            break
        time.sleep(20)


if __name__ == "__main__":
    d = datetime.now()
    start = f"{d.month:02d}/{d.day:02d}/{d.year} 02:00 PM -0400"
    stop  = f"{d.month:02d}/{d.day:02d}/{d.year} 11:59 PM -0400"

    collect('raw_data', None, stop)
