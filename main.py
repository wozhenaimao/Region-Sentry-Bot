import os
import difflib
import re

import discord
from discord import app_commands
from dotenv import load_dotenv

from src.foxhole import FoxholeAPI

load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()


@tree.command(
    name="region",
    description="Get live region data. :name: name of the region (text value)",
)
async def first_command(interaction: discord.Interaction, name: str):

    await interaction.response.defer()

    realNameList = difflib.get_close_matches(name.replace(' ', '') + 'Hex', FoxholeAPI.maps().json())

    if len(realNameList) == 0:
        await interaction.followup.send(f"Region named '{name}' not found")
        return

    realName: str = realNameList[0]
    regionImagePath = FoxholeAPI.hex_to_image(realName)

    mapData = FoxholeAPI.map(realName).json()

    e = discord.Embed(
        title = f'Region “{re.sub(r"(\w)([A-Z])", r"\1 \2", realName.replace('Hex', ''))}” info',
        description = f'Regional data on the {mapData['dayOfWar']}th day of war',
        color = discord.Colour.from_rgb(21, 38, 18)
    )
    e.add_field(
        name='Total Enlistments',
        value=f'About {mapData['totalEnlistments']} people have enlisted here',
        inline=False
    )
    e.add_field(
        name='Total Casualties',
        value=f'Colonials: {mapData['colonialCasualties']}\nWardens: {mapData['wardenCasualties']}',
        inline=False
    )
    f = discord.File(f'temp/{regionImagePath}.png', filename="image.png")
    e.set_image(url='attachment://image.png')
    e.set_footer(text='This is an open source project')

    await interaction.followup.send(file=f, embed=e)

    os.remove(f'temp/{regionImagePath}.png')


client.run(os.getenv('DISCORD_BOT_TOKEN'))
