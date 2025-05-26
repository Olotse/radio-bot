import discord
from discord import ui

class MusicControls(ui.View):
    def __init__(self, interaction, voice_client):
        super().__init__()
        self.interaction = interaction
        self.voice_client = voice_client

    @ui.button(label="Play/Pause", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: ui.Button):
        if self.voice_client.is_playing():
            self.voice_client.pause()
            await interaction.response.send_message(f"Lecture en pause : {self.current_title}", ephemeral=True)
            await self.update_last_message(self.interaction, f"Lecture en pause : {self.current_title}\n\nListe de lecture :\n{self.get_play_queue()}", view=self)
        else:
            self.voice_client.resume()
            await interaction.response.send_message(f"Lecture reprise : {self.current_title}", ephemeral=True)
            await self.update_last_message(self.interaction, f"Lecture reprise : {self.current_title}\n\nListe de lecture :\n{self.get_play_queue()}", view=self)

    @ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: ui.Button):
        self.voice_client.stop()
        self.play_queue.clear()  # Vider la liste de lecture
        self.current_title = None  # Réinitialiser la musique en cours
        await interaction.response.send_message("Lecture arrêtée et liste de lecture vidée.", ephemeral=True)
        await self.update_last_message(self.interaction, "Lecture arrêtée et liste de lecture vidée.\n\nListe de lecture :\n" + self.get_play_queue(), view=None)

    @ui.button(label="Skip", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: ui.Button):
        if self.play_queue:
            self.voice_client.stop()
            await interaction.response.send_message("Musique passée.", ephemeral=True)
            await self.update_last_message(self.interaction, "Musique passée.\n\nListe de lecture :\n" + self.get_play_queue(), view=self)
            await self.play_next(self.interaction, self.voice_client)
        else:
            await interaction.response.send_message("La liste de lecture est vide.", ephemeral=True)
            await self.update_last_message(self.interaction, "La liste de lecture est vide.\n\nListe de lecture :\n" + self.get_play_queue(), view=self)
