import random


def handleResponse(message: str) -> str:
    msg = message.lower()

    # Ping Pong
    if msg == 'ping':
        return 'pong'

    # Roll a dice
    if msg == 'roll':
        return str(random.randint(1, 6))

    # Help message
    if msg == 'help':
        return '`This is a help message that can be changed.`'
