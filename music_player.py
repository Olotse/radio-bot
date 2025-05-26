import asyncio
import logging

import discord

import yt_dlp as youtube_dl
from ui_components import MusicControls

class MusicPlayer:
    def __init__(self):
        self.play_queue = []
        self.current_title = None
        self.last_message = None
        self.cookie_filepath = 'res/cookies.txt'
        self.audio_quality = '5'

        with open('.env', 'r', encoding='utf-8') as env:
            lines = env.readlines()

            for line in lines:
                if line.find('COOKIES') != -1:
                    self.cookie_filepath = line.removeprefix('COOKIES="').removesuffix('"\n')
                    continue
                elif line.find('AUDIO_QUALITY') != -1:
                    self.audio_quality = line.removeprefix('AUDIO_QUALITY="').removesuffix('"\n')

    async def update_last_message(self, interaction, content, view=None):
        try:
            if self.last_message:
                await self.last_message.edit(content=content, view=view)
            else:
                self.last_message = await interaction.followup.send(content, view=view)
        except Exception as e:
            logging.exception(e)
            self.last_message = await interaction.followup.send(content, view=view)

    async def send_temporary_message(self, interaction, content):
        try:
            message = await interaction.followup.send(content)
            await asyncio.sleep(2)  # Attendre 2 secondes
            await message.delete()
        except Exception as e:
            logging.exception(e)

    def get_play_queue(self):
        if self.current_title:
            queue_list = [f"En cours de lecture : {self.current_title}"]
        else:
            queue_list = []

        if self.play_queue:
            queue_list.extend([f"{i+1}. {title}" for i, (url, title) in enumerate(self.play_queue)])
        else:
            queue_list.append("La liste de lecture est vide.")

        return "\n".join(queue_list)

    async def play_next(self, interaction, voice_client):
        if self.play_queue:
            url, title = self.play_queue.pop(0)
            self.current_title = title
            voice_client.play(discord.FFmpegPCMAudio(url))
            await self.update_last_message(interaction, f'Lecture de : {title}\n\nListe de lecture :\n{self.get_play_queue()}', view=MusicControls(interaction, voice_client))
            while voice_client.is_playing():
                await asyncio.sleep(1)
            await self.play_next(interaction, voice_client)
        else:
            self.current_title = None
            await self.update_last_message(interaction, "La liste de lecture est vide.\n\nListe de lecture :\n" + self.get_play_queue(), view=MusicControls(interaction, voice_client))

    async def play(self, interaction, url):
        await interaction.response.defer()

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
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self.audio_quality,
            }],
            'cookiefile': self.cookie_filepath,
            'quiet': True
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)

                if 'entries' in info:
                    await self.update_last_message(interaction, f'Ajout de la playlist à la liste de lecture : {info["title"]}\n\nListe de lecture :\n{self.get_play_queue()}', view=MusicControls(interaction, voice_client))

                    playlist_opts = {
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': self.audio_quality,
                        }],
                        'quiet': True
                    }

                    with youtube_dl.YoutubeDL(playlist_opts) as playlist_dl:
                        for entry in info['entries']:
                            try:
                                video_info = playlist_dl.extract_info(entry['url'], download=False)
                                if 'url' in video_info:
                                    self.play_queue.append((video_info['url'], video_info.get('title', 'Titre inconnu')))
                                    await self.update_last_message(interaction, f'Ajout de la playlist à la liste de lecture : {info["title"]}\n\nListe de lecture :\n{self.get_play_queue()}', view=MusicControls(interaction, voice_client))

                            except Exception as e:
                                logging.exception(f"Erreur lors de l'extraction d'une vidéo de la playlist : {e}")

                else:
                    if 'url' in info:
                        self.play_queue.append((info['url'], info.get('title', 'Titre inconnu')))
                        await self.update_last_message(interaction, f'Ajout de la musique à la liste de lecture : {info.get("title", "Titre inconnu")}\n\nListe de lecture :\n{self.get_play_queue()}', view=MusicControls(interaction, voice_client))

                if not self.current_title:
                    if voice_client.is_playing():
                        voice_client.stop()

                    await self.play_next(interaction, voice_client)
            except Exception as e:
                if str(e).find("--cookies") != -1:
                    await interaction.followup.send(f"Cookies expirés", ephemeral=True)
                    logging.exception(f"Une erreur avec les cookies est survenue : {e}")
                else:
                    await interaction.followup.send(f"Une erreur est survenue : {e}", ephemeral=True)
                    logging.exception(f"Une erreur est survenue : {e}")
