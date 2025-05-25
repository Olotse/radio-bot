# coding=utf-8

import asyncio
from warnings import catch_warnings

import discord
from discord.ext import commands
from discord import app_commands, ui

import io

import yt_dlp as youtube_dl

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Assurez-vous que cet intent est activé dans le portail des développeurs

bot = commands.Bot(command_prefix='!', intents=intents)

# Liste de lecture globale
play_queue = []
current_title = None  # Variable pour stocker le titre de la musique actuellement en cours de lecture
last_message = None  # Variable pour stocker le dernier message envoyé par le bot

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

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
    await interaction.response.defer()  # Indique que la réponse sera envoyée plus tard

    if not interaction.user.voice:
        await interaction.followup.send("Vous n'êtes pas dans un canal vocal.")
        return

    voice_channel = interaction.user.voice.channel
    if interaction.guild.voice_client is None:
        await voice_channel.connect()
    elif interaction.guild.voice_client.channel != voice_channel:
        await interaction.guild.voice_client.move_to(voice_channel)

    voice_client = interaction.guild.voice_client

    ydl_opts = {
        'format': 'bestaudio/best',
        'extract_flat': 'in_playlist',
        'quiet': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:  # C'est une playlist
                await update_last_message(interaction, f'Ajout de la playlist à la liste de lecture : {info["title"]}\n\nListe de lecture :\n{get_play_queue()}', view=MusicControls(interaction, voice_client))

                playlist_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True
                }

                with youtube_dl.YoutubeDL(playlist_opts) as playlist_dl:
                    for entry in info['entries']:
                        try:
                            video_info = playlist_dl.extract_info(entry['url'], download=False)
                            if 'url' in video_info:
                                play_queue.append((video_info['url'], video_info.get('title', 'Titre inconnu')))
                                await update_last_message(interaction,
                                                              f'Ajout de la playlist à la liste de lecture : {info["title"]}\n\nListe de lecture :\n{get_play_queue()}',
                                                              view=MusicControls(interaction, voice_client))

                        except Exception as e:
                            print(f"Erreur lors de l'extraction d'une vidéo de la playlist : {e}")

            else:  # C'est une seule vidéo
                if 'url' in info:
                    play_queue.append((info['url'], info.get('title', 'Titre inconnu')))
                    await update_last_message(interaction, f'Ajout de la musique à la liste de lecture : {info.get("title", "Titre inconnu")}\n\nListe de lecture :\n{get_play_queue()}', view=MusicControls(interaction, voice_client))

            # Jouer la première musique de la liste si le bot n'est pas déjà en train de jouer
            if not voice_client.is_playing() and not current_title:
                await play_next(interaction, voice_client)
        except Exception as e:
            await interaction.followup.send(f"Une erreur est survenue : {e}")

async def play_next(interaction, voice_client):
    global current_title, last_message
    if play_queue:
        url, title = play_queue.pop(0)
        current_title = title  # Stocker le titre de la musique actuellement en cours de lecture
        voice_client.play(discord.FFmpegPCMAudio(url))
        await update_last_message(interaction, f'Lecture de : {title}\n\nListe de lecture :\n{get_play_queue()}', view=MusicControls(interaction, voice_client))
        while voice_client.is_playing():
            await asyncio.sleep(1)
        # Jouer la prochaine musique une fois la lecture terminée
        await play_next(interaction, voice_client)
    else:
        await update_last_message(interaction, "La liste de lecture est vide.\n\nListe de lecture :\n" + get_play_queue(), view=MusicControls(interaction, voice_client))

# Lancer le bot
envIOWrapper = io.open('./.env')

lines = envIOWrapper.readlines()
token = ''

for line in lines:
    if line.find('TOKEN') != -1:
        token = line.removeprefix('TOKEN="').removesuffix('"')

if len(token) > 0:
    try:
        bot.run(token)
    except Exception as e:
        print(e)
        print("token: " + token)
