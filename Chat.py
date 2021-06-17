import re
from datetime import datetime
from socket import socket
from typing import Tuple, Union

_SERVER = "irc.chat.twitch.tv"
_PORT = 6667
_FETCH_PATTERN = r":(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #{join_username} :(.*)"


class Chat:
    """
    Class wrapper around a socket to stream from a Twitch chat
    """

    def __init__(self, login_username: str, join_username: str, auth_token: str) -> None:
        """
        Constructor

        This class uses sockets to stream messages from a specified Twitch
        chat. The connection is issued on construction.

        A Twitch account is required, alongside an OAuth token for Twitch IRC.
        You can obtain one here: https://twitchapps.com/tmi/

        Twitch Developer Documentation can be found here: https://dev.twitch.tv/docs/

        Parameters
        ----------
        login_username: str
            Your Twitch username or channel name

        join_username: str
            Username or channel name of the chat to stream from

        auth_token: str
            Twitch IRC OAuth token  
        """
        self.__join_username = join_username
        self.__sock = socket()
        self.__sock.connect((_SERVER, _PORT))
        self.__sock.send(f"PASS {auth_token}\n".encode("utf-8"))
        self.__sock.send(f"NICK {login_username}\n".encode("utf-8"))
        self.__sock.send(f"JOIN #{join_username}\n".encode("utf-8"))
        for _ in range(5):
            self.__sock.recv(2048)

    def fetch(self, buff_size: int = 2048) -> Union[Tuple[str, str, datetime], None]:
        sent = datetime.now()
        try:
            resp = self.__sock.recv(buff_size).decode("utf-8")
        except UnicodeDecodeError:
            return None

        if resp.startswith("PING"):
            self.__sock.send("PONG\n".encode("utf-8"))
            return None

        match = re.search(_FETCH_PATTERN.format(
            join_username=self.__join_username), resp.strip())

        if match is None:
            return None
        return match.groups() + (sent,)
