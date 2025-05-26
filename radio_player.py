import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import re

class RadioPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.radio_streams = []

    async def autocomplete_stations(self, interaction: discord.Interaction, current: str):
        # Filtrer les stations en fonction de ce que l'utilisateur a tapé
        filtered_stations = [stream.split('|')[1] for stream in self.radio_streams if current.lower() in stream.lower()]

        # Retourner les 25 premières suggestions
        return [app_commands.Choice(name=station, value=station) for station in filtered_stations[:25]]

    def extract_streams_from_sii(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Utiliser une expression régulière pour extraire les URLs
        pattern = r'stream_data\[\d+\]: "([^"]+)"'
        urls = re.findall(pattern, content)

        return urls

    @commands.Cog.listener()
    async def on_ready(self):
        file_path = "res/live_streams.sii"

        with open('.env', 'r', encoding='utf-8') as env:
            lines = env.readlines()

            for line in lines:
                if line.find('LIVE_STREAMS') != -1:
                    file_path = line.removeprefix('LIVE_STREAMS="').removesuffix('"\n')

        self.radio_streams = self.extract_streams_from_sii(file_path)
        print(f'Logged in as {self.bot.user.name}')

    @app_commands.command(name='stations', description='Lister les stations de radio disponibles')
    @app_commands.describe(station="Nom de la station de radio")
    @app_commands.autocomplete(station=autocomplete_stations)
    async def stations(self, interaction: discord.Interaction, station: str):
        await self.play_station(interaction, station)

    async def play_station(self, interaction, station_name):
        # Vérifier si l'utilisateur est connecté à un canal vocal
        if not interaction.user.voice:
            await interaction.response.send_message("Vous devez être connecté à un canal vocal pour utiliser cette commande.", ephemeral=True)
            return

        # Trouver la station correspondante
        selected_station = None
        for stream in self.radio_streams:
            if station_name.lower() in stream.lower():
                selected_station = stream
                break

        if selected_station:
            stream_url = selected_station.split('|')[0]
            voice_channel = interaction.user.voice.channel
            voice = await voice_channel.connect()
            voice.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=stream_url))
            await interaction.response.send_message(f"Lecture de la station : {selected_station.split('|')[1]}", ephemeral=True)
        else:
            await interaction.response.send_message("Station non trouvée.", ephemeral=True)

#async def setup(bot):
#    await bot.add_cog(RadioPlayer(bot))

def setup(bot):
    asyncio.run(bot.add_cog(RadioPlayer(bot)))