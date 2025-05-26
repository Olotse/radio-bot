import logging
import io

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
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logging.exception(e)

async def update_last_message(interaction, content, view=None):
    global last_message
    try:
        if last_message:
            await last_message.edit(content=content, view=view)
        else:
            last_message = await interaction.followup.send(content, view=view)
    except discord.errors.NotFound:
        # Si le message n'est pas trouvé, envoyez un nouveau message
        last_message = await interaction.followup.send(content, view=view)

async def send_temporary_message(interaction, content):
    try:
        message = await interaction.followup.send(content)
        await asyncio.sleep(2)  # Attendre 2 secondes
        await message.delete()
    except discord.errors.NotFound:
        # Si le message n'est pas trouvé, ne faites rien
        pass

class MusicControls(ui.View):
    def __init__(self, interaction, voice_client):
        super().__init__()
        self.interaction = interaction
        self.voice_client = voice_client

    @ui.button(label="Play/Pause", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: ui.Button):
        global current_title, last_message
        if self.voice_client.is_playing():
            self.voice_client.pause()
            await interaction.response.send_message(f"Lecture en pause : {current_title}", ephemeral=True)
            await update_last_message(self.interaction, f"Lecture en pause : {current_title}\n\nListe de lecture :\n{get_play_queue()}", view=self)
        else:
            self.voice_client.resume()
            await interaction.response.send_message(f"Lecture reprise : {current_title}", ephemeral=True)
            await update_last_message(self.interaction, f"Lecture reprise : {current_title}\n\nListe de lecture :\n{get_play_queue()}", view=self)

    @ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: ui.Button):
        global last_message, play_queue, current_title
        self.voice_client.stop()
        play_queue.clear()  # Vider la liste de lecture
        current_title = None  # Réinitialiser la musique en cours
        await interaction.response.send_message("Lecture arrêtée et liste de lecture vidée.", ephemeral=True)
        await update_last_message(self.interaction, "Lecture arrêtée et liste de lecture vidée.\n\nListe de lecture :\n" + get_play_queue(), view=None)

    @ui.button(label="Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: ui.Button):
        global last_message
        if play_queue:
            self.voice_client.stop()
            await interaction.response.send_message("Musique passée.", ephemeral=True)
            await update_last_message(self.interaction, "Musique passée.\n\nListe de lecture :\n" + get_play_queue(), view=self)
            await play_next(self.interaction, self.voice_client)
        else:
            await interaction.response.send_message("La liste de lecture est vide.", ephemeral=True)
            # Garder les boutons affichés même si la liste de lecture est vide
            await update_last_message(self.interaction, "La liste de lecture est vide.\n\nListe de lecture :\n" + get_play_queue(), view=self)

def get_play_queue():
    global current_title
    if current_title:
        queue_list = [f"En cours de lecture : {current_title}"]
    else:
        queue_list = []

    if play_queue:
        queue_list.extend([f"{i+1}. {title}" for i, (url, title) in enumerate(play_queue)])
    else:
        queue_list.append("La liste de lecture est vide.")

    return "\n".join(queue_list)

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
                token = line.removeprefix('TOKEN="').removesuffix('"')

if len(token) > 0:
    try:
        bot.run(token)
    except Exception as e:
        logging.exception(e)
        logging.info("token: " + token)
    if len(token) > 0:
        try:
            bot.run(token)
        except Exception as e:
            logging.exception(e)
            logging.info("token: " + token)

if __name__ == "__main__":
    main()
