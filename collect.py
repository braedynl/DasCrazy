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
REQUEST_HEADERS = {"Client-Id": CLIENT_ID,
                   "Authorization": f"Bearer {BEARER_TOKEN}"}

# Response-parsing pattern
SEARCH_PATTERN = re.compile(":(.*)!.* PRIVMSG #%s :(.*)" % BROADCASTER_LOGIN)


def get_metadata() -> Tuple[str, str]:
    """
    Fetch the broadcast's game name and title

    Returns
    -------
    Tuple[str, str]
        The game name and title, respectively
    """
    try:
        data = requests.get(REQUEST_URL, headers=REQUEST_HEADERS).json()['data'][0]
        return data['game_name'], data['title']
    except Exception as e:
        print("Error occured while fetching metadata:", e)
    return 'UNKNOWN', 'UNKNOWN'


def main():
    df = pd.read_csv('data/real.csv')

    sock = socket()
    sock.connect((SERVER, PORT))

    sock.send(f"PASS oauth:{IRC_TOKEN}\n".encode("utf-8"))
    sock.send(f"NICK {PERSONAL_LOGIN}\n".encode("utf-8"))
    sock.send(f"JOIN #{BROADCASTER_LOGIN}\n".encode("utf-8"))

    resp = sock.recv(1024).decode("utf-8")
    if "Welcome" not in resp:
        print("Connection to Twitch IRC failed, response:")
        print(resp)
        return

    print("Connection to Twitch IRC successful, entering main loop...")
    print("Use CTRL + C to stop at anytime\n")

    row_temp = {"sent": '', "game_name": '',
                "title": '', "user": '', "message": ''}

    try:
        while True:
            resp = sock.recv(1024).decode("utf-8", errors='ignore')

            if resp.startswith("PING"):
                sock.send("PONG\n".encode("utf-8"))
                print(f"Pong issued at {datetime.now()}")
                continue

            match = SEARCH_PATTERN.search(resp)

            if match is None:
                continue

            # A blanket search for just "peepoHas" is done here to save
            # time before another recv() call; further classification
            # to find if it's truly a "das crazy" moment is done in post

            user, message = match.groups()

            if "peepoHas" in message:
                sent = datetime.now()
                game_name, title = get_metadata()

                # It's slightly faster to declare a dictionary first, and set its values later
                # as opposed to initializating a dictionary with values
                row_temp["sent"] = sent
                row_temp["game_name"] = game_name
                row_temp["title"] = title
                row_temp["user"] = user
                row_temp["message"] = message.replace('\n', ' ').replace('\r', '')

                df = df.append(row_temp, ignore_index=True)

                print(f"peepoHas found at {sent}")

                # Did you know two chained replace() calls is faster than
                # any other method to replace two substrings? Crazy...

    except KeyboardInterrupt:
        print("Closing socket and exporting data...")

        sock.close()
        df.to_csv('data/real.csv', index=False)

        print("Done.")


if __name__ == "__main__":
    main()
