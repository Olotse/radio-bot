import logging

import discord
from discord.ext import commands
from discord import app_commands

from music_player import MusicPlayer
from radio_player import RadioPlayer, setup as radioPlayerSetup

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
music_player = MusicPlayer()
radio_player = RadioPlayer(bot)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    try:
        #await radioPlayerSetup(bot)
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logging.exception(e)

@bot.tree.command(name='play', description='Ajouter une musique ou une playlist à la liste de lecture depuis un lien YouTube')
@app_commands.describe(url='Lien YouTube de la musique ou de la playlist')
async def play(interaction: discord.Interaction, url: str):
    await music_player.play(interaction, url)

def main():
    token = ''

    with open('.env', 'r', encoding='utf-8') as env:
        lines = env.readlines()

        for line in lines:
            if line.find('TOKEN') != -1:
                token = line.removeprefix('TOKEN="').removesuffix('"\n')

    if len(token) > 0:
        try:
            radioPlayerSetup(bot)
            bot.run(token)
        except Exception as e:
            logging.exception(e)
            logging.info("token: " + token)

if __name__ == "__main__":
    main()
