import re
import sys
import time
import warnings
from datetime import datetime
from socket import socket
from typing import Annotated, Union

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


def log(msg: str) -> None:
    sys.stdout.write(f"[{datetime.now()}] {msg}\n")


def irc_connect() -> socket:

    for timeout in (2, 4, 8, 16, -1):
        sock = socket()

        try:
            sock.connect((SERVER, PORT))

            sock.send(f"PASS oauth:{IRC_TOKEN}\n".encode("utf-8"))
            sock.send(f"NICK {PERSONAL_LOGIN}\n".encode("utf-8"))
            sock.send(f"JOIN #{BROADCASTER_LOGIN}\n".encode("utf-8"))

            resp = sock.recv(1024).decode("utf-8", errors="ignore")

            if resp.startswith(f":tmi.twitch.tv 001 {PERSONAL_LOGIN} :Welcome, GLHF!"):
                log("Connection to Twitch IRC successful, entering main loop...")
                log("Use CTRL + C to stop at anytime\n--")
                return sock

            log("Twitch IRC freaked out, attempting restart...")

        except ConnectionResetError:
            log("Connection was forcibly closed by the host, attempting restart...")

        sock.close()

        if timeout == -1:
            resp = resp.replace("\n", "").replace("\r", "")
            raise RuntimeError(f"could not connect to Twitch IRC\nResponse: {resp}")

        time.sleep(timeout)


def fetch_metadata() -> tuple[str, str]:
    resp = requests.get(REQUEST_URL, headers=REQUEST_HEADERS)

    if resp.status_code == 200:
        metadata = resp.json()["data"][0]
        return metadata["game_name"], metadata["title"]

    warnings.warn(f"metadata fetch request unsuccessful, response: {resp}")
    return "", ""


def collect(filename: str, start: Union[str, None], stop: str, format: str, refresh_every: Annotated[float, "minutes"] = 15) -> None:

    def collect_helper(delta: float) -> int:
        sock = irc_connect()
        game_name, title = fetch_metadata()

        df = pd.read_csv(f"data/{filename}.csv")
        row_template = {
            "sent": "",
            "game_name": "",
            "title": "",
            "user": "",
            "message": "",
        }

        state = 0
        time_end = time.time() + delta

        try:
            while time.time() < time_end:
                resp = sock.recv(2048).decode("utf-8", errors="ignore")

                if resp.startswith("PING"):
                    sock.send("PONG\n".encode("utf-8"))
                    log("PING")
                    continue

                for user, message in SEARCH_PATTERN.findall(resp):

                    if "peepoHas" in message:

                        # Declaring a dictionary and setting its values later is faster than
                        # creating a dictionary with initial values
                        row_template["sent"] = datetime.now()
                        row_template["game_name"] = game_name
                        row_template["title"] = title
                        row_template["user"] = user
                        row_template["message"] = message

                        df = df.append(row_template, ignore_index=True)

                        log(f"Keyword found in message by {user}")

        except KeyboardInterrupt:
            state = -1

        log("Closing socket and exporting data...")

        sock.close()
        df.to_csv(f"data/{filename}.csv", index=False)

        log("Done.")

        return state

    if start is not None:
        sleep_for = datetime.strptime(start, format).timestamp() - time.time()
        if sleep_for < 0:
            warnings.warn("starting datetime has already passed, collection starting now...")
        else:
            log(f"Starting collection in {sleep_for} seconds...")
            time.sleep(sleep_for)

    ts_end = datetime.strptime(stop, format).timestamp()

    while time.time() < ts_end:
        if collect_helper(refresh_every * 60) < 0:
            break
        time.sleep(15)


if __name__ == "__main__":
    d = datetime.now()
    start = f"{d.month:02d}/{d.day:02d}/{d.year} 02:00 PM -0400"
    stop = f"{d.month:02d}/{d.day:02d}/{d.year} 11:59 PM -0400"
    format = "%m/%d/%Y %I:%M %p %z"

    collect("raw_data", start, stop, format)
