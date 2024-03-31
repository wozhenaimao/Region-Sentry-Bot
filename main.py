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
    description="Get real region data. :name: name of the region (text value)",
)
async def first_command(interaction: discord.Interaction, name: str):

    await interaction.response.defer()

    realNameList = difflib.get_close_matches(name.replace(' ', '') + 'Hex', FoxholeAPI.maps().json())

    if len(realNameList) == 0:
        await interaction.followup.send(f"Region named '{name}' not found")
        return

    realName: str = realNameList[0]
    regionImagePath, regionColor, regionType = FoxholeAPI.hex_to_image(realName)

    mapData = FoxholeAPI.map(realName).json()

    if regionColor == FoxholeAPI.COLONIALS:
        color = discord.Colour.from_rgb(122, 156, 116)
    elif regionColor == FoxholeAPI.WARDENS:
        color = discord.Colour.from_rgb(12, 69, 171)
    else:
        color = discord.Colour.from_rgb(140, 140, 140)

    e = discord.Embed(
        title = f'**Region “{re.sub(fr"({chr(92)}w)([A-Z])", fr"{chr(92)}1 {chr(92)}2", realName.replace("Hex", ""))}” info**',
        description = f'Regional data on the __{mapData["dayOfWar"]}th__ day of war.\nRegion status: {regionType}',
        color = color
    )
    e.add_field(
        name='• Total **Enlistments**',
        value=f'About __{mapData['totalEnlistments']} people__ have enlisted here',
        inline=False
    )
    e.add_field(
        name='• Total **Casualties**',
        value=f'Colonials: __{mapData['colonialCasualties']}__\nWardens: __{mapData['wardenCasualties']}__',
        inline=False
    )
    f = discord.File(f'temp/{regionImagePath}.png', filename="image.png")
    e.set_image(url='attachment://image.png')

    warData = FoxholeAPI.war().json()
    e.set_footer(text=f'War №{warData['warNumber']}')

    await interaction.followup.send(file=f, embed=e)

    os.remove(f'temp/{regionImagePath}.png')


@tree.command(
    name="map",
    description="Get real image of the entire map! Be aware, this function will take a while to run",
)
async def first_command(interaction: discord.Interaction):

    await interaction.response.defer()

    mapImagePath, totalEnlistments, totalColonialCasualties, totalWardenCasualties, totalCasualties = FoxholeAPI.map_image()
    warData = FoxholeAPI.war().json()
    
    e = discord.Embed(
        title = f'**Real data of the entire battlefield**',
        description = f'Conquest started at __{warData['conquestStartTime']}__ (UNIX timestamp)',
        color = discord.Colour.from_rgb(255, 255, 255)
    )
    e.add_field(
        name='**General information**',
        value=f'Total enlistments: __{totalEnlistments}__\nTotal casualties: __{totalCasualties}__\nColonial casualties: __{totalColonialCasualties}__\nWarden casualties: __{totalWardenCasualties}__',
        inline=False
    )
    f = discord.File(f'temp/{mapImagePath}.jpg', filename="image.jpg")
    e.set_image(url='attachment://image.jpg')
    e.set_footer(text=f'War №{warData['warNumber']} See the image above for complete details of the entire map')

    await interaction.followup.send(file=f, embed=e)

    os.remove(f'temp/{mapImagePath}.jpg')


client.run(os.getenv('DISCORD_BOT_TOKEN'))
