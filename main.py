import os
import random
import discord
import datetime
import requests
import matplotlib.pyplot as plt
from math import ceil
from discord.ext import commands
from dotenv import load_dotenv
from prisma import Prisma

load_dotenv()  # Load .env file

# Load environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
NEWS_API = os.getenv('NEWS_API_KEY')
WEATHER_API = os.getenv('WEATHER_API_KEY')

# Global variables
message_count = 0
channel_message_count = {}

# Create intents & bot
bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())  # Create bot


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
@bot.event
async def on_ready():
    await connectToDB()
    # Success message (terminal only)
    print(f'{bot.user} is now online.')


# Actions for when a user joins the server
@bot.event
async def on_member_join(member):
    await createUser(member)  # Create database entry for user


# Actions for when a user sends a message
@bot.event
async def on_message(message):
    global message_count

    # Check if message is from a bot
    if message.author.bot:
        return

    await awardXp(message.author.name, 3, message.channel.id)  # (username, xp, channel_id)

    # Get or create channel
    channel = await prisma.channel.find_first(where={'id': message.channel.id})
    if channel is None:
        channel = await prisma.channel.create(
            data={'id': message.channel.id, 'name': message.channel.name, 'messages': 1},
        )
    else:
        channel = await prisma.channel.update(
            where={'id': message.channel.id},
            data={'messages': channel.messages + 1},
        )

    # continue
    await bot.process_commands(message)


# Commands

# Clear - Clears a specified amount of messages (cmd_clear)
@bot.command()
# @commands.has_any_role("Moderator", "Administrator", "Owner")
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)  # Clear messages


# Hello - Says hello to the user (cmd_hello)
@bot.command()
async def hello(ctx):
    username = ctx.message.author.mention  # Mention user
    await ctx.reply(f'Hello {username}!')


# Ping - Returns the bots latency (cmd_ping)
@bot.command()
async def ping(ctx):
    await ctx.reply(f'Pong! {round(bot.latency * 1000)}ms')  # Round latency


# Total users in database (cmd_totalusers)
@bot.command()
async def totalusers(ctx):
    totalUsers = await prisma.user.count()  # Count the number of users in the database
    await ctx.reply(f'There are {totalUsers} users in the database')


'''
    MODERATION COMMANDS
'''


# Ban - Bans a user (cmd_ban)
@bot.command()
@commands.has_any_role("Moderator", "Administrator", "Owner")
async def ban(ctx, member: discord.Member, *, reason: str = ""):
    if reason == "":
        reason = "This user was banned by " + ctx.message.author.name
    await member.ban(reason=reason)


# Kick - Kicks a user (cmd_kick)
@bot.command()
#@commands.has_any_role("Moderator", "Administrator", "Owner")
async def kick(ctx, member: discord.Member, *, reason: str = ""):
    if reason == "":
        reason = "This user was kicked by " + ctx.message.author.name
    await member.kick(reason=reason)


# Mute - Mutes a user (cmd_mute)
@bot.command()
# @commands.has_any_role("Moderator", "Administrator", "Owner")
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
@bot.command()
#@commands.has_any_role("Moderator", "Administrator", "Owner")
async def unmute(ctx, member: discord.Member):
    await member.edit(timed_out_until=None)


# Info - Displays all the commands available to use with this bot (cmd_info)
@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title="Info",
        description="This command displays all the commands available to use with this bot",
        color=0x02F0FF)

    # Add fields
    embed.add_field(
        name="?ban",
        value="This command bans a user",
        inline=False)
    embed.add_field(
        name="?kick",
        value="This command removes a user from the server but doesnt ban them", inline=False)
    embed.add_field(
        name="?mute",
        value="This command places the user on a time out for a set amount of time",
        inline=False)
    embed.add_field(
        name="?unmute",
        value="This command removes the amount of time left on a users timout",
        inline=False)
    embed.add_field(
        name="?news",
        value="This command displays top headlines from the news API",
        inline=False)
    embed.add_field(
        name="?weather",
        value="This command displays the current weather of a location",
        inline=False)
    embed.add_field(
        name="?poll",
        value="This command starts a poll with a prompt and options to choose from",
        inline=False)
    embed.add_field(
        name="?channelStats",
        value="This command shows a bar chart of the message count per channel",
        inline=False)
    embed.add_field(
        name="?hello",
        value="This command greets the user",
        inline=False)
    embed.add_field(
        name="?pollResults",
        value="This command shows the results of a poll using the poll ID",
        inline=False)
    embed.add_field(
        name="?clear",
        value="This command clears a specified amount of messages",
        inline=False)
    embed.add_field(
        name="?info",
        value="This command displays all the commands available to use with this bot",
        inline=False)
    embed.add_field(
        name="?ping",
        value="This command displays the latency of the bot",
        inline=False)
    embed.add_field(
        name="?totalusers",
        value="This command displays how many users are in the database",
        inline=False)
    embed.add_field(
        name="?xp",
        value="This command displays the xp of a user",
        inline=False)
    embed.add_field(
        name="?leaderboard",
        value="This command displays the top 10 users with the most xp",
        inline=False)
    embed.add_field(
        name="?rank",
        value="This command displays the rank of a user",
        inline=False)
    embed.add_field(
        name="?xp_give",
        value="This command gives xp to a user",
        inline=False)
    embed.add_field(
        name="?roll [coins] [expected winning side]",
        value="This command rolls a dice and allows you to bet coins on the result",
        inline=False)
    embed.add_field(
        name="?coinflip [coins]",
        value="This command flips a coin and allows you to bet coins on the result",
        inline=False)
    embed.add_field(
        name="?roulette [coins]",
        value="This command spins a roulette wheel and allows you to bet coins on the result",
        inline=False)
    embed.add_field(
        name="?8ball [question]",
        value="This command answers a question with a random response",
        inline=False)
    embed.add_field(
        name="?coins",
        value="This command displays the amount of coins a user has",
        inline=False)

    # Send the embed to the channel
    await ctx.reply(embed=embed)


'''
    NEWS
'''


# News - Displays the top three current articles from their api
@bot.command()
async def news(ctx):
    url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'country': 'us',  # Country for the news
        'apiKey': NEWS_API,
        'pageSize': 3  # The number of results displayed
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


'''
    EXPERIENCE POINTS SYSTEM
'''


# XP - Displays the user's XP and level (cmd_xp)
@bot.command()
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
        await bot.get_channel(channel_id).send(embed=embed)


# Manually give a user xp (cmd_xp_give)
@bot.command()
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
        data={'coins': {'decrement': int(coins)}}  # Add coins
    )


# Determine user's rank (cmd_rank)
@bot.command()
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
@bot.command()
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


@bot.command()
async def topThree(ctx):
    # Get the top 3 users by XP
    users = await prisma.user.find_many(
        skip=0,  # Skip the first 0 users
        take=3,  # Take the top 3 users
        order={'xp': 'desc'}  # Order the users by XP in descending order
    )

    usernames = [user.username for user in users]
    xp_values = [user.xp for user in users]

    # Code to make the graph
    plt.bar(usernames, xp_values, color="blue")
    plt.xlabel('Players')
    plt.ylabel('XP')
    plt.title('Top Three Players by XP')
    plt.savefig('top_three.png')
    plt.close()

    # Send the image to the Discord channel
    with open('top_three.png', 'rb') as f:
        file = discord.File(f)
        await ctx.send(file=file)


"""
    GAMES COMMANDS
"""


@bot.command()
async def rps(ctx, user_move):
    # create a list of moves
    moves = ['rock', 'paper', 'scissors']

    # check for a valid move
    if user_move not in moves:
        await ctx.send('thats not a move, next time pick rock, paper or scissors')
        return

    # bot picks a move at random from the list
    bot_move = random.choice(moves)

    # If else statements that will check win conditions for user and award coins if they do
    if user_move == bot_move:
        await ctx.send(f"I choose {bot_move}, It's a tie!")
    elif (user_move == 'rock' and bot_move == 'scissors'):
        await ctx.send(f"I choose {bot_move}, You win 5 coins!")
        await addCoins(ctx.message.author.name, 5, ctx.message.channel.id)
    elif (user_move == 'paper' and bot_move == 'rock'):
        await ctx.send(f"I choose {bot_move}, You win 5 coins!")
        await addCoins(ctx.message.author.name, 5, ctx.message.channel.id)
    elif (user_move == 'scissors' and bot_move == 'paper'):
        await ctx.send(f"I choose {bot_move}, You win 5 coins!")
        await addCoins(ctx.message.author.name, 5, ctx.message.channel.id)
    else:
        await ctx.send(f"I choose {bot_move}, I win!")


# Check if the user has enough coins to bet
async def checkCoins(username):
    # Get user's coins
    user = await prisma.user.find_first(
        where={'username': username},  # Find user in database
    )

    return user.coins


# Roll - Rolls a die and returns a random number (cmd_roll), user can also bet coins on a number and win/lose coins
@bot.command()
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
@bot.command(aliases=['8ball'])
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
@bot.command()
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
@bot.command(aliases=['flip'])
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
@bot.command()
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
    await bot.get_channel(channel_id).send(embed=embed)


"""
STATS AND GRAPHS
"""


# Channel stats - Displays a bar graph of the number of messages per channel (cmd_channel_stats)
@bot.command(aliases=['channelstats'])
async def channelStats(ctx):
    # Fetch channel message counts from database
    prisma_channels = await prisma.channel.find_many()
    channels = [channel.name for channel in prisma_channels]
    counts = [channel.messages for channel in prisma_channels]

    # Plot bar chart
    plt.bar(channels, counts, color="blue")
    plt.xlabel('Channel')
    plt.ylabel('Message Count')
    plt.title('Most Popular Channels')
    plt.xticks(rotation=45)

    # Save plot to file and send to Discord
    plt.savefig('channel_message_count.png', bbox_inches='tight')
    plt.clf()
    with open('channel_message_count.png', 'rb') as f:
        picture = discord.File(f)
        await ctx.send(file=picture)


# Weather - Displays the current weather in a location (cmd_weather)
@bot.command()
async def weather(ctx, *, location: str):
    weather_api = WEATHER_API

    url = f'http://api.weatherapi.com/v1/current.json?key={weather_api}&q={location}&aqi=no'

    try:
        response = requests.get(url)
        data = response.json()
        if 'error' in data:
            await ctx.reply(f'Error: {data["error"]["message"]}')
        else:
            # Where we fill desired info from json into our vairables.
            location_name = data['location']['name']
            temperature_F = data['current']['temp_f']
            condition = data['current']['condition']['text']
            icon = data['current']['condition']['icon']

            # Set Up the the data pulled from api into an array
            embed = discord.Embed(title=f'Current Weather in {location_name}', color=0x3498db)
            embed.add_field(name='Temperature (°F)', value=f'{temperature_F}°F', inline=False)
            embed.add_field(name='Condition', value=condition, inline=False)
            embed.set_thumbnail(url=f'https:{icon}')
            await ctx.reply(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.reply(f'Error: {e}')


# Poll - Creates a poll (cmd_poll)
@bot.command()
async def poll(ctx, prompt, *options):
    embed = discord.Embed(title="Question: ", description=prompt, color=0x02F0FF)

    for i, option in enumerate(options):
        embed.add_field(name=f"Option {chr(0x1f1e6 + i)}: " + option, value="", inline=False)

    poll_message = await ctx.send(embed=embed)
    for i in range(len(options)):
        await poll_message.add_reaction(chr(0x1f1e6 + i))

    embed.set_footer(text=f"Poll ID: {poll_message.id}")
    await poll_message.edit(embed=embed)


# Poll Results - Displays the results of a poll (cmd_poll_results)
@bot.command()
async def pollResults(ctx, poll_id: int):
    poll_message = None

    # limit for the message to reduce load on the bot and reduce time taken to execute
    async for message in ctx.channel.history(limit=100):
        if message.embeds and message.embeds[0].footer.text == f"Poll ID: {poll_id}":
            poll_message = message
            break

    if poll_message:
        # split the option line but using a colon to setparate the field
        options = [field.name.split(': ')[1] for field in poll_message.embeds[0].fields]
        reactions = poll_message.reactions
        # the bot has to add one reaction to each option so we subtract one to get the total
        # total votes is counted int order to see if there are any votes in the poll
        total_votes = sum([reaction.count - 1 for reaction in reactions])
        vote_counts = [reaction.count - 1 for reaction in reactions]

        # make a graph if there are reactions in the poll
        if total_votes > 0:
            plt.pie(vote_counts, labels=options, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title("Poll Results")
            plt.savefig('poll_chart.png')
            plt.clf()
            
            poll_chart = discord.File('poll_chart.png')
            await ctx.reply(file=poll_chart)
        else:
            await ctx.reply("There are 0 vots in this poll, tray again after people vote!")
    else:
        await ctx.reply("Cant find that poll, check that the poll ID")


bot.run(TOKEN)  # Run the bot
