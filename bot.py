import os
import discord
import responses
from dotenv import load_dotenv

load_dotenv()  # Load .env file


async def sendMessage(message, userMessage, isPrivate):
    try:
        # Handle the response
        res = responses.handleResponse(userMessage)
        await message.author.send(res) if isPrivate else await message.channel.send(res)

    except Exception as e:
        # Error message (terminal only)
        print(e)


def runDiscordBot():
    # Load environment variables
    TOKEN = os.getenv('DISCORD_TOKEN')
    CMD_PREFIX = os.getenv('DISCORD_CMD_PREFIX')

    # Create intents
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)  # Create client

    # On ready
    @client.event
    async def on_ready():
        # Success message (terminal only)
        print(f'{client.user} has connected to Discord!')

    # On message
    @client.event
    async def on_message(message):
        # Ignore messages from the bot
        if message.author == client.user:
            return

        # Save important information
        username = str(message.author).split('#')[0]
        userMessage = str(message.content)
        channel = str(message.channel)

        # Debugging only
        print(f'{username} sent a message in {channel}: {userMessage}')

        # Determine if the message is a command or not
        if userMessage.startswith(CMD_PREFIX):

            # Remove the command prefix and pass the command to the handler
            await sendMessage(message, userMessage[1:], False)
        else:
            # Do nothing if not a command
            pass

    client.run(TOKEN)  # Run the bot
