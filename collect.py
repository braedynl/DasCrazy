from Chat import Chat
from keys import AUTH_TOKEN

LOGIN_USERNAME = "braedynl_"
JOIN_USERNAME = "hasanabi"

stream = Chat(LOGIN_USERNAME, JOIN_USERNAME, AUTH_TOKEN)

while True:
    username, message, dt = stream.fetch()

    print(f'{username}: {message}')
