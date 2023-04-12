import os

import discord
from dotenv import load_dotenv
from prisma import Prisma

import responses

load_dotenv()  # Load .env file


# Have bot send a message in the channel
async def sendMessage(message, userMessage, isPrivate):
    try:
        # Handle the response
        res = responses.handleResponse(userMessage)
        await message.author.send(res) if isPrivate else await message.channel.send(res)

    except Exception as e:
        # Error message (terminal only)
        print(e)


# Run the bot
def runDiscordBot():
    # Connect to database
    prisma = Prisma()
    await prisma.connect()

    # Load environment variables
    TOKEN = os.getenv('DISCORD_TOKEN')
    CMD_PREFIX = os.getenv('DISCORD_CMD_PREFIX')

    # Create intents
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)  # Create client

    # Declare bot as connected to Discord
    @client.event
    async def on_ready():
        # Success message (terminal only)
        print(f'{client.user} has connected to Discord!')

    # Handle creating database entry on join
    @client.event
    async def on_member_join(member):
        # Create database entry for user
        await prisma.user.create(
            data={
                'id': member.id,  # Set id as Discord ID
                'name': member.name,  # Set name as Discord name (Ryan#1234)
            }
        )

    # Handle message sent from Discord User
    @client.event
    async def on_message(message):
        # Ignore messages from the bot itself
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
