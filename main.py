import os
import random
from math import ceil

import discord
import datetime
import requests
from discord.ext import commands
from dotenv import load_dotenv
from prisma import Prisma

# from newsapi import newsapi_client

load_dotenv()  # Load .env file

# Load environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
CMD_PREFIX = os.getenv('DISCORD_CMD_PREFIX')

# Create intents & client
client = commands.Bot(command_prefix="?", intents=discord.Intents.all())  # Create client


# Create Prisma instance & connect to DB
async def connectToDB():
    global prisma
    prisma = Prisma()
    await prisma.connect()
    print('Prisma: Connected to Railway')


# Function to add user to database
async def createUser(username):
    # Create database entry for user
    await prisma.user.create(
        data={'username': username}  # Set username as Discord name (Ryan#1234)}
    )
    # Success message (terminal only)
    print(f'Prisma: Created new entry for {username}')


# Actions for when the bot connects to Discord
@client.event
async def on_ready():
    await connectToDB()
    # Success message (terminal only)
    print(f'{client.user} is now online.')


# Actions for when a user joins the server
@client.event
async def on_member_join(member):
    await createUser(member)  # Create database entry for user


# Actions for when a user sends a message
@client.event
async def on_message(message):
    # Check if message is from a bot
    if message.author.bot:
        return

    # Award user 3 XP for every message sent
    await awardXp(message.author.name, 3, message.channel.id)  # (username, xp, channel_id)

    # continue
    await client.process_commands(message)


# Commands

# Clear - Clears a specified amount of messages (cmd_clear)
@client.command()
# @commands.has_any_role("Moderator", "Administrator", "Owner")
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)  # Clear messages


# Hello - Says hello to the user (cmd_hello)
@client.command()
async def hello(ctx):
    username = ctx.message.author.mention  # Mention user
    await ctx.reply(f'Hello {username}!')


# Ping - Returns the bots latency (cmd_ping)
@client.command()
async def ping(ctx):
    await ctx.reply(f'Pong! {round(client.latency * 1000)}ms')  # Round latency


# Total users in database (cmd_totalusers)
@client.command()
async def totalusers(ctx):
    totalUsers = await prisma.user.count()  # Count the number of users in the database
    await ctx.reply(f'There are {totalUsers} users in the database')


'''
    MODERATION COMMANDS
'''


# Ban - Bans a user (cmd_ban)
@client.command()
@commands.has_any_role("Moderator", "Administrator", "Owner")
async def ban(ctx, member: discord.Member, *, reason: str = ""):
    if reason == "":
        reason = "This user was banned by " + ctx.message.author.name
    await member.ban(reason=reason)


# Kick - Kicks a user (cmd_kick)
@client.command()
@commands.has_any_role("Moderator", "Administrator", "Owner")
async def kick(ctx, member: discord.Member, *, reason: str = ""):
    if reason == "":
        reason = "This user was kicked by " + ctx.message.author.name
    await member.kick(reason=reason)


# Mute - Mutes a user (cmd_mute)
@client.command()
@commands.has_any_role("Moderator", "Administrator", "Owner")
async def mute(ctx, member: discord.Member, timeLimit):
    # Filter seconds
    if "s" in timeLimit:
        getTime = timeLimit.strip("s")
        if int(getTime) > 2419000:
            await ctx.send("The time amount cannot be bigger than 28 days")
        else:
            newTime = datetime.timedelta(seconds=int(getTime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newTime)

    # Filter minutes
    elif "m" in timeLimit:
        getTime = timeLimit.strip("m")
        if int(getTime) > 40320:
            await ctx.send("The time amount cannot be bigger than 28 days")
        else:
            newTime = datetime.timedelta(minutes=int(getTime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newTime)

    # Filter hours
    elif "h" in timeLimit:
        getTime = timeLimit.strip("h")
        if int(getTime) > 672:
            await ctx.send("The time amount cannot be bigger than 28 days")
        else:
            newTime = datetime.timedelta(minutes=int(getTime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newTime)

    # Filter days
    elif "d" in timeLimit:
        getTime = timeLimit.strip("d")
        if int(getTime) > 28:
            await ctx.send("The time amount cannot be bigger than 28 days")
        else:
            newTime = datetime.timedelta(minutes=int(getTime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newTime)

    # Filter weeks
    elif "w" in timeLimit:
        getTime = timeLimit.strip("w")
        if int(getTime) > 4:
            await ctx.send("The time amount cannot be bigger than 28 days")
        else:
            newTime = datetime.timedelta(minutes=int(getTime))
            await member.edit(timed_out_until=discord.utils.utcnow() + newTime)


# Unmute - Unmutes a user (cmd_unmute)
@client.command()
@commands.has_any_role("Moderator", "Administrator", "Owner")
async def unmute(ctx, member: discord.Member):
    await member.edit(timed_out_until=None)


# Info - Displays all the commands available to use with this bot (cmd_info)
@client.command()
async def info(ctx):
    embed = discord.Embed(title="Info",
                          description="This command displays all the commands available to use with this bot",
                          color=0x02F0FF)
    embed.add_field(name="!ban",
                    value="This command bans a user",
                    inline=False)
    embed.add_field(name="!kick",
                    value="This command removes a user from the server but doesnt ban them",
                    inline=False)
    embed.add_field(name="!mute",
                    value="This command places the user on a time out for a set amount of time",
                    inline=False)
    embed.add_field(name="!unmute",
                    value="This command removes the amount of time left on a users timout",
                    inline=False)
    await ctx.send(embed=embed)

    # delete user's message
    await ctx.message.delete()


'''
    NEWS
'''


# News - Displays the top 5 news articles from the US (cmd_news)
@client.command()
async def news(ctx):
    url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'country': 'us',  # Specify the country for which you want news
        'apiKey': os.getenv("API_KEY_NEWS"),
        'pageSize': 3  # Specify the number of articles you want
    }
    response = requests.get(url, params=params)
    data = response.json()

    articles = data['articles']
    for article in articles:
        title = article['title']
        description = article['description']
        url = article['url']

        # Create an embed with the article information
        embed = discord.Embed(title=title, description=description, color=0x02F0FF)
        embed.add_field(name='Read More', value=url, inline=False)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)

    # delete user's message
    await ctx.message.delete()


'''
    EXPERIENCE POINTS SYSTEM
'''


# XP - Displays the user's XP and level (cmd_xp)
@client.command()
async def xp(ctx, username=None):
    # Get user's own XP and level
    if username is None:
        user = await prisma.user.find_first(
            where={'username': ctx.message.author.name},  # Find user in database
        )

        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'{ctx.message.author.name}\'s XP',
                              description=f'XP: {user.xp} | Level: {user.level}',
                              color=0x02F0FF)

    # Get another user's XP and level
    else:
        user = await prisma.user.find_first(
            where={'username': username},  # Find user in database
        )

        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'{username}\'s XP',
                              description=f'XP: {user.xp} | Level: {user.level}',
                              color=0x02F0FF)

    # Send the embed to the Discord channel
    await ctx.reply(embed=embed)


# Award XP - Awards XP to a user (cmd_xp_award)
async def awardXp(username, xp, channel_id):
    # Give user XP
    await prisma.user.update(
        where={'username': username},  # Find user in database
        data={'xp': {'increment': xp}}  # Add XP
    )

    # Get user's current level
    user = await prisma.user.find_first(
        where={'username': username},  # Find user in database
    )

    # Calculate the level based on the XP
    # level = int(user.xp ** (1 / 5))

    # Calculate level as XP / 150
    level = int(user.xp / (100 * (user.level + 1 * 1.5)))

    # Check if the user has leveled up
    if level > user.level:
        # Update the user's level
        await prisma.user.update(
            where={'username': username},  # Find user in database
            data={'level': level}  # Set level to new level
        )
        # Success message (terminal only)
        print(f'Prisma: {username} has leveled up to level {level}!')

        # Generate an embed to send in the channel
        embed = discord.Embed(
            title="Level Up!",
            description=f"{username} has leveled up to level {level}!",
            color=discord.Color.green()
        )

        # Send the embed in the original channel
        await client.get_channel(channel_id).send(embed=embed)


# Manually give a user xp (cmd_xp_give)
@client.command()
async def xp_give(ctx, username, xp):
    # Give user XP
    await awardXp(username, int(xp), ctx.message.channel.id)

    # delete user's message
    await ctx.message.delete()


# Give coins - Awards coins to a user (cmd_coins_award)
async def addCoins(username, coins, channel_id):
    # Give user coins
    await prisma.user.update(
        where={'username': username},  # Find user in database
        data={'coins': {'increment': coins}}  # Add coins
    )


# Take coins - Awards coins to a user (cmd_coins_award)
async def takeCoins(username, coins, channel_id):
    # Give user coins
    await prisma.user.update(
        where={'username': username},  # Find user in database
        data={'coins': {'decrement': coins}}  # Add coins
    )


# Determine user's rank (cmd_rank)
@client.command()
async def rank(ctx, username=None):
    # Get user's own XP and level
    if username is None:
        user = await prisma.user.find_first(
            where={'username': ctx.message.author.name},  # Find user in database
        )

        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'{ctx.message.author.name}\'s Rank',
                              description=f'Rank: {user.rank}',
                              color=0x02F0FF)

    # Get another user's XP and level
    else:
        user = await prisma.user.find_first(
            where={'username': username},  # Find user in database
        )

        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'{username}\'s Rank',
                              description=f'Rank: {user.rank}',
                              color=0x02F0FF)

    # Send the embed to the Discord channel
    await ctx.reply(embed=embed)


# Leaderboard - Displays the top 10 users by xp earned (cmd_leaderboard)
@client.command()
async def leaderboard(ctx):
    # Get the top 10 users by xp
    users = await prisma.user.find_many(
        skip=0,  # Skip the first 0 users
        take=10,  # Take the top 10 users
        order={'xp': 'desc'}  # Order the users by xp in descending order
    )

    # Generate an embed to send in the channel
    embed = discord.Embed(title='Server Leaderboard', color=0x02F0FF)

    count = 1

    # Add each user to the embed
    for user in users:
        embed.add_field(name=f'{count}. {user.username}', value=f'XP: {user.xp} | Level: {user.level}', inline=False)
        count += 1

    # Send the embed to the Discord channel
    await ctx.reply(embed=embed)


"""
    GAMES COMMANDS
"""


# Check if the user has enough coins to bet
async def checkCoins(username):
    # Get user's coins
    user = await prisma.user.find_first(
        where={'username': username},  # Find user in database
    )

    return user.coins


# Roll - Rolls a die and returns a random number (cmd_roll), user can also bet coins on a number and win/lose coins
@client.command()
async def roll(ctx, bet=None, number=None):
    balance = await checkCoins(ctx.message.author.name)

    # Check if the user has bet any coins
    if bet is None:
        # Generate a random number between 1 and 6
        number = random.randint(1, 6)

        # Generate an embed to send in the channel
        embed = discord.Embed(title='Roll',
                              description=f'You rolled a {number}!',
                              color=0x02F0FF)

        # Award 5 xp
        await awardXp(ctx.message.author.name, 5, ctx.message.channel.id)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)

    # Check if the user has bet any coins
    else:
        # Check if the user has entered a number
        if number is None:
            # Generate an embed to send in the channel
            embed = discord.Embed(title='Roll',
                                  description=f'You must enter a number to bet on!',
                                  color=0x02F0FF)

            # Send the embed to the Discord channel
            await ctx.reply(embed=embed)

        # Check if the user has bet a valid number
        elif int(number) < 1 or int(number) > 6:
            # Generate an embed to send in the channel
            embed = discord.Embed(title='Roll',
                                  description=f'You must enter a number between 1 and 6 to bet on!',
                                  color=0x02F0FF)

            # Send the embed to the Discord channel
            await ctx.reply(embed=embed)

        # Check if the user has bet a valid number of coins
        elif int(bet) < 1:
            # Generate an embed to send in the channel
            embed = discord.Embed(title='Roll',
                                  description=f'You must bet at least 1 coin!',
                                  color=0x02F0FF)

            # Send the embed to the Discord channel
            await ctx.reply(embed=embed)

        # Check if the user has enough coins to bet
        elif balance < int(bet):
            # Generate an embed to send in the channel
            embed = discord.Embed(title='Roll',
                                  description=f'Not enough coins!',
                                  color=0x02F0FF)

            # Send the embed to the Discord channel
            await ctx.reply(embed=embed)

        else:
            # Generate a random number between 1 and 6
            roll = random.randint(1, 6)

            # Check if the user won the bet
            if int(number) == roll:
                # Generate an embed to send in the channel
                embed = discord.Embed(title='Roll',
                                      description=f'You rolled a {roll} and won {int(bet) * 6} coins! You now have {balance + int(bet) * 6} coins!',
                                      color=0x02F0FF)

                # Award 10 xp
                await awardXp(ctx.message.author.name, 10, ctx.message.channel.id)

                # Add coins to user's balance
                await addCoins(ctx.message.author.name, int(bet) * 6, ctx.message.channel.id)

                # Send the embed to the Discord channel
                await ctx.reply(embed=embed)

                print(f'{ctx.message.author.name} won {int(bet) * 6} coins!')

            # Check if the user lost the bet
            else:
                # Generate an embed to send in the channel
                embed = discord.Embed(title='Roll',
                                      description=f'You rolled a {roll} and lost {bet} coins! You now have {balance - int(bet)} coins!',
                                      color=0x02F0FF)

                # Award 5 xp
                await awardXp(ctx.message.author.name, 5, ctx.message.channel.id)

                # Remove coins from user's balance
                await takeCoins(ctx.message.author.name, int(bet), ctx.message.channel.id)

                # Send the embed to the Discord channel
                await ctx.reply(embed=embed)

                print(f'{ctx.message.author.name} lost {int(bet)} coins!')


# 8 Ball - Answers a question (cmd_8ball)
@client.command(aliases=['8ball'])
async def _8ball(ctx, *, question):
    responses = [
        'It is certain.',
        'It is decidedly so.',
        'Without a doubt.',
        'Yes – definitely.',
        'You may rely on it.',
        'As I see it, yes.',
        'Most likely.',
        'Outlook good.',
        'Yes.',
        'Signs point to yes.',
        'Reply hazy, try again.',
        'Ask again later.',
        'Better not tell you now.',
        'Cannot predict now.',
        'Concentrate and ask again.',
        "Don't count on it.",
        'My reply is no.',
        'My sources say no.',
        'Outlook not so good.',
        'Very doubtful.'
    ]

    # generate reply as an embed
    embed = discord.Embed(title=f'Question: {question}',
                          description=f'Answer: {random.choice(responses)}',
                          color=0x02F0FF)
    await ctx.reply(embed=embed)


# Roulette with coin betting system (cmd_roulette)
@client.command()
async def roulette(ctx, bet):
    # Get user's own coins
    balance = await checkCoins(ctx.message.author.name)

    # Check if user has enough coins
    if balance < int(bet):
        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'Insufficient Coins',
                              description=f'You only have {balance} coins!',
                              color=0x02F0FF)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)
        return

    # Generate a random number
    number = random.randint(0, 6)

    # Generate winning number
    winning_number = random.randint(0, 6)

    print(f'Roulette: {ctx.message.author.name} rolled {number} and the winning number is {winning_number}')

    await awardXp(ctx.message.author.name, 15, ctx.message.channel.id)  # Award XP

    # Check if user won
    if number != winning_number:
        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'Roulette',
                              description=f'You lost {bet} coins. Your balance is now: {balance - int(bet)} coins.',
                              color=0x02F0FF)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)

        # Take user's coins
        await takeCoins(ctx.message.author.name, bet, ctx.message.channel.id)
    else:
        # multiply bet
        bet = ceil(int(bet) * 3)

        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'Roulette',
                              description=f'You **won** {bet} coins! Your balance is now: {balance + int(bet)} coins.',
                              color=0x02F0FF)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)

        # Give user coins
        await addCoins(ctx.message.author.name, bet, ctx.message.channel.id)


# Coinflip with coin betting system (cmd_coinflip)
@client.command(aliases=['flip'])
async def coinflip(ctx, bet):
    balance = await checkCoins(ctx.message.author.name)

    # make sure bet is more than 0
    if int(bet) <= 0:
        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'Invalid Bet',
                              description=f'Your bet must be at least 1 coin!',
                              color=0x02F0FF)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)
        return

    # Check if user has enough coins
    if balance < int(bet):
        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'Insufficient Coins',
                              description=f'You only have {balance} coins!',
                              color=0x02F0FF)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)
        return

    # Generate a random number
    number = random.randint(0, 1)

    # Generate winning number
    winning_number = random.randint(0, 1)

    print(f'Coinflip: {ctx.message.author.name} flipped {number} and the winning number is {winning_number}')

    # Award some xp
    await awardXp(ctx.message.author.name, 10, ctx.message.channel.id)

    # Check if user won
    if number != winning_number:
        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'Coinflip',
                              description=f'You lost {bet} coins. Your balance is now: {balance - int(bet)} coins.',
                              color=0x02F0FF)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)

        # Take user's coins
        await takeCoins(ctx.message.author.name, int(bet), ctx.message.channel.id)
    else:
        # Generate an embed to send in the channel
        embed = discord.Embed(title=f'Coinflip',
                              description=f'You **won** {bet} coins! Your balance is now: {balance + int(bet)} coins.',
                              color=0x02F0FF)

        # Send the embed to the Discord channel
        await ctx.reply(embed=embed)

        # Give user coins
        await addCoins(ctx.message.author.name, int(bet), ctx.message.channel.id)


"""
COINS SYSTEM
"""


# Coins - Displays the user's own coins (cmd_coins)
@client.command()
async def coins(ctx):
    user = await prisma.user.find_first(
        where={'username': ctx.message.author.name},  # Find user in database
    )

    # Generate an embed to send in the channel
    embed = discord.Embed(title=f'{ctx.message.author.name}\'s Coins',
                          description=f'Coins: {user.coins}',
                          color=0x02F0FF)

    # Send the embed to the Discord channel
    await ctx.reply(embed=embed)


# Award Coins - Awards coins to a user (cmd_coins_award)
async def awardCoins(username, coins, channel_id):
    # Give user coins
    await prisma.user.update(
        where={'username': username},  # Find user in database
        data={'coins': {'increment': coins}}  # Add coins
    )

    # Success message (terminal only)
    print(f'Prisma: {username} has been awarded {coins} coins!')

    # Generate an embed to send in the channel
    embed = discord.Embed(
        title="Coins Awarded!",
        description=f"{username} has been awarded {coins} coins!",
        color=discord.Color.green()
    )

    # Send the embed in the original channel
    await client.get_channel(channel_id).send(embed=embed)


client.run(TOKEN)  # Run the bot
