import os
import re
import time
import warnings
from datetime import datetime
from socket import socket
from typing import Annotated, Any

import requests

from keys import BEARER_TOKEN, CLIENT_ID, IRC_TOKEN
from util import load, log

# User information
PERSONAL_LOGIN = "braedynl_"
BROADCASTER_LOGIN = "hasanabi"

# API stuff
SERVER = "irc.chat.twitch.tv"
PORT = 6667
REQUEST_URL = f"https://api.twitch.tv/helix/streams?user_login={BROADCASTER_LOGIN}"
REQUEST_HEADERS = {"Client-Id": CLIENT_ID, "Authorization": f"Bearer {BEARER_TOKEN}"}

# IRC response pattern
SEARCH_PATTERN = re.compile(f":(.*)!.* PRIVMSG #{BROADCASTER_LOGIN} :(.*)\r\n")

# TODO: use logging module?


def fetch_metadata() -> tuple[bool, dict[str, Any]]:
    """
    Fetch Twitch stream metadata

    Returns:
        tuple[bool, dict[str, Any]]: Whether the user is live, and the
            stream metadata respectively.

    Notes:
        Uses the "Get Streams" endpoint, see API documentation for
        more details: https://dev.twitch.tv/docs/api/reference#get-streams
    """

    resp = requests.get(REQUEST_URL, headers=REQUEST_HEADERS).json()

    if "data" in resp:
        if len(resp["data"]) > 0:
            metadata = resp["data"][0]
            return metadata["type"] == "live", metadata
        return False, {}

    warnings.warn(f"fetch request failed ({resp['status']}: {resp['message']})")
    return False, {}


def irc_connect() -> socket:
    """
    Connect to Twitch chat IRC

    Returns:
        socket.socket: Twitch chat IRC socket

    Raises:
        RuntimeError: If connection fails after five attempts
    """

    for timeout in (2, 4, 8, 16, -1):
        irc = socket()

        try:
            irc.connect((SERVER, PORT))

            irc.send(f"PASS oauth:{IRC_TOKEN}\n".encode("utf-8"))
            irc.send(f"NICK {PERSONAL_LOGIN}\n".encode("utf-8"))
            irc.send(f"JOIN #{BROADCASTER_LOGIN}\n".encode("utf-8"))

            resp = irc.recv(1024).decode("utf-8", errors="ignore")

            if resp.startswith(f":tmi.twitch.tv 001 {PERSONAL_LOGIN} :Welcome, GLHF!"):
                log("Established connection to Twitch IRC")
                return irc

            log("Twitch IRC freaked out, attempting restart...")

        except ConnectionResetError:
            log("Connection reset error, attempting restart...")

        irc.close()

        if timeout == -1:
            resp = resp.replace("\n", "").replace("\r", "")
            raise RuntimeError(f"could not connect to Twitch IRC\nResponse: {resp}")

        time.sleep(timeout)


def collect(filename: str, refresh_every: Annotated[float, "minutes"] = 15) -> int:
    """
    Collect messages from Twitch chat containing the text, `"peepoHas"`.

    Runs from stream start to stream end by periodically checking the user's
    live status. Begins collection instantly if stream is live, otherwise waits.

    Args:
        filename: Name of the raw data file
        refresh_every: Time span before periodic login refresh

    Returns:
        int: -1 if `KeyboardInterrupt`, 0 if stream went offline
    """

    def collect_helper(irc: socket, metadata: dict[str, Any]) -> int:
        df = load(filename)
        row_template = {
            "sent": "",
            "game_name": "",
            "title": "",
            "user": "",
            "message": "",
        }
        state = 0
        time_end = time.time() + (refresh_every * 60)

        try:
            while time.time() < time_end:
                resp = irc.recv(2048).decode("utf-8", errors="ignore")

                if resp.startswith("PING"):
                    irc.send("PONG\n".encode("utf-8"))
                    log("PING")
                    continue

                for user, message in SEARCH_PATTERN.findall(resp):

                    if "peepoHas" in message:

                        # Declaring a dictionary and setting its values later is faster than
                        # creating a dictionary with initial values
                        row_template["sent"] = datetime.now()
                        row_template["game_name"] = metadata["game_name"]
                        row_template["title"] = metadata["title"]
                        row_template["user"] = user
                        row_template["message"] = message

                        df = df.append(row_template, ignore_index=True)

                        log(f"Keyword found in message by {user}")

        except KeyboardInterrupt:
            state = -1

        # TODO: handle ConnectionAbortedError (thrown when wifi goes out)

        log("Exporting data...")
        df.to_csv(f"data/{filename}.csv", index=False)
        log("Done.")

        return state

    log("Waiting for user to go live...")
    is_live, metadata = False, {}
    while True:
        is_live, metadata = fetch_metadata()
        if is_live:
            break
        log("Live status checked")
        time.sleep(900)

    log("User is live, beginning collection...")
    while True:
        irc = irc_connect()
        state = collect_helper(irc, metadata)
        irc.close()

        if state < 0:
            return -1

        is_live, metadata = fetch_metadata()

        if not is_live:
            return 0

        time.sleep(3)


if __name__ == "__main__":
    state = collect("raw")

    # Sometimes I gotta hit the bed before Hasan ends stream, so I let
    # the script run and shutdown my computer afterwards
    if state == 0:
        os.system("shutdown -s")
