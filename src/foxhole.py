import requests
import random
from pprint import pprint
from time import time
import re

from PIL import Image, ImageDraw, ImageFont

from static.items import ITEMS


class FoxholeAPI:
    """ 
    Accurate to 30/03/24
    https://github.com/clapfoot/warapi/tree/master
    """

    WORLD_EXTENT_MINIMUM = (-109199.999997, -94499.99999580906968410989)
    WORLD_EXTENT_MAXIMUM = (109199.999997, 94499.99999580906968410989)
    API_URL = [ # Shard option
        'https://war-service-live.foxholeservices.com/api',
        'https://war-service-live-2.foxholeservices.com/api',
        'https://war-service-live-3.foxholeservices.com/api'
    ]
    HEX_SIZE = (1024, 888)
    ICON_SIZE = (1024, 888)
    COLONIALS = 'COLONIALS'
    WARDENS = 'WARDENS'
    NONE = 'NONE'
    BASE_ZONE_RADIUS = 150
    FONT_HEX = ImageFont.truetype('static/font.ttf', 60)
    FONT_MAJOR = ImageFont.truetype('static/font.ttf', 20)
    FONT_MINOR = ImageFont.truetype('static/font.ttf', 10)


    def __init__(self) -> None:

        self.mapsGeneralData = {}
        self.mapsStaticData = {}
        self.mapsDynamicData = {}
        self.calculatedInfo = {}
        self.shard = 1


    def war(shard: int) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL[shard - 1] + '/worldconquest/war')
    

    def maps(shard: int) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL[shard - 1] + '/worldconquest/maps')
    

    def map(name: str, shard: int) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL[shard - 1] + f'/worldconquest/warReport/{name}')
    

    def map_static(name: str, shard: int) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL[shard - 1] + f'/worldconquest/maps/{name}/static')


    def map_dynamic(name: str, shard: int) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL[shard - 1] + f'/worldconquest/maps/{name}/dynamic/public')
    

    def hex_to_image(self, name: str, isImage: bool = False, quick: bool = False):
        """
        Returns unique path id of the image
        """

        startTime = time()

        mapGeneralData = self.mapsGeneralData.get(name)
        mapStaticData = self.mapsStaticData.get(name)
        mapDynamicData = self.mapsDynamicData.get(name)

        mapPath = 'static/Images/Maps/Map' + name + '.TGA'

        hexImage = Image.open(
            fp=mapPath
        ).convert('RGBA')

        basesCount = 0
        hasColonialBases = False
        hasWardenBases = False

        for item in mapDynamicData['mapItems']:
            iconName = ITEMS.get(item['iconType'])
            if not iconName:
                raise Exception('[ERROR] could not find image for an item', item)
            if not 'base' in iconName.lower():
                continue
            position = (
                FoxholeAPI.HEX_SIZE[0] * item['x'],
                FoxholeAPI.HEX_SIZE[1] * item['y']
            )
            circleImage = Image.new(
                'RGBA',
                (FoxholeAPI.BASE_ZONE_RADIUS * 2, FoxholeAPI.BASE_ZONE_RADIUS * 2)
            )
            circle = ImageDraw.Draw(circleImage)
            circle.ellipse(
                (
                    0,
                    0,
                    FoxholeAPI.BASE_ZONE_RADIUS * 2,
                    FoxholeAPI.BASE_ZONE_RADIUS * 2
                ), 
                fill=(84, 152, 72, 50) if item['teamId'] == FoxholeAPI.COLONIALS else (16, 92, 228, 50) if item['teamId'] == FoxholeAPI.WARDENS else (255, 255, 255, 50)
            )
            mask = hexImage.copy()
            position = (int(position[0] - FoxholeAPI.BASE_ZONE_RADIUS), int(position[1] - FoxholeAPI.BASE_ZONE_RADIUS))
            hexImage.alpha_composite(circleImage, position)
            hexImage = Image.composite(hexImage, hexImage, mask=mask)
            del circle
        
        for item in mapDynamicData['mapItems']:

            position = (
                FoxholeAPI.HEX_SIZE[0] * item['x'],
                FoxholeAPI.HEX_SIZE[1] * item['y']
            )

            iconName = ITEMS.get(item['iconType'])
            if not iconName:
                raise Exception('[ERROR] could not find image for an item', item)
                    
            if 'base' in iconName.lower():
                if item['teamId'] == FoxholeAPI.COLONIALS:
                    hasColonialBases = True
                    basesCount += 1
                elif item['teamId'] == FoxholeAPI.WARDENS:
                    hasWardenBases = True
                    basesCount -= 1
                else:
                    if basesCount > 0:
                        basesCount -= 1
                    elif basesCount < 0:
                        basesCount += 1

            if quick:
                continue

            mapIconPath = 'static/Images/MapIcons/MapIcon' + iconName + '.TGA'
            
            try:
                itemImage = Image.open(
                    fp=mapIconPath
                ).convert('RGBA')
            except FileNotFoundError:
                raise Exception('[ERROR] File does not exist...', item, mapIconPath)

            R, G, B, A = itemImage.split()
            match item['teamId']:
                case FoxholeAPI.COLONIALS:
                    itemImage = Image.merge('RGBA', (R.point(lambda p: p  - 150), G.point(lambda p: p  - 100), B.point(lambda p: p  - 150), A))
                case FoxholeAPI.WARDENS:
                    itemImage = Image.merge('RGBA', (R.point(lambda p: p  - 199), G.point(lambda p: p  - 123), B.point(lambda p: p  - 50), A))

            position = (int(position[0] - itemImage.width / 2), int(position[1] - itemImage.height / 2))
            hexImage.alpha_composite(itemImage, position)

        color = FoxholeAPI.NONE
        regionType = 'active frontline'

        R, G, B, A = hexImage.split()
        if basesCount > 5:
            color = FoxholeAPI.COLONIALS
            if hasWardenBases and isImage:
                hexImage = Image.merge('RGBA', (R.point(lambda p: p  - 100), G.point(lambda p: p  - 66), B.point(lambda p: p  - 100), A))
            else:
                regionType = 'Colonials\' controlled territory'
                hexImage = Image.merge('RGBA', (R.point(lambda p: p  - 66), G.point(lambda p: p  - 44), B.point(lambda p: p  - 66), A))
        elif basesCount < -5:
            color = FoxholeAPI.WARDENS
            if hasColonialBases and isImage:
                hexImage = Image.merge('RGBA', (R.point(lambda p: p  - 132), G.point(lambda p: p  - 81), B.point(lambda p: p  - 32), A))
            else:
                regionType = 'Wardens\' controlled territory'
                hexImage = Image.merge('RGBA', (R.point(lambda p: p  - 88), G.point(lambda p: p  - 54), B.point(lambda p: p  - 21), A))
        
        if basesCount > 5 and hasWardenBases:
            regionType = 'frontline mostly controlled by Colonials'
        if basesCount < -5 and hasColonialBases:
            regionType = 'frontline mostly controlled by Wardens'

        if isImage:
            text = re.sub(fr"({chr(92)}w)([A-Z])", fr"{chr(92)}1 {chr(92)}2", name.replace("Hex", ""))
            itemImage = Image.new('RGBA', FoxholeAPI.HEX_SIZE)
            font = FoxholeAPI.FONT_HEX
            draw = ImageDraw.Draw(itemImage)
            draw.text((FoxholeAPI.HEX_SIZE[0] // 2 - len(text) * 60 // 4, FoxholeAPI.HEX_SIZE[1] // 2 - 35), text, font = font, align ="center", color = (255, 255, 255, 255))
            position = (
                FoxholeAPI.HEX_SIZE[0] * 0.5,
                FoxholeAPI.HEX_SIZE[1] * 0.5
            )
            position = (int(position[0] - itemImage.width / 2), int(position[1] - itemImage.height / 2))
            hexImage.alpha_composite(itemImage, position)
            return hexImage, mapGeneralData['totalEnlistments'], mapGeneralData['colonialCasualties'], mapGeneralData['wardenCasualties']

        for item in mapStaticData['mapTextItems']:
            text = item['text']
            itemImage = Image.new('RGBA', FoxholeAPI.HEX_SIZE)
            font = FoxholeAPI.FONT_MAJOR if item['mapMarkerType'] == 'Major' else FoxholeAPI.FONT_MINOR
            draw = ImageDraw.Draw(itemImage)
            draw.text((FoxholeAPI.HEX_SIZE[0] // 2 - len(text) * (20 if item['mapMarkerType'] == 'Major' else 10) // 4, FoxholeAPI.HEX_SIZE[1] // 2 - (2 if item['mapMarkerType'] == 'Major' else 1)), text, font = font, align ="center", color = (255, 255, 255, 255) if item['mapMarkerType'] == 'Major' else (100, 100, 100, 255))
            position = (
                FoxholeAPI.HEX_SIZE[0] * item['x'],
                FoxholeAPI.HEX_SIZE[1] * item['y']
            )
            position = (int(position[0] - itemImage.width / 2), int(position[1] - itemImage.height / 2))
            hexImage.alpha_composite(itemImage, position)

        pathId = random.randint(10000000, 99999999)
        hexImage.save(f'temp/{pathId}.png')

        return pathId, color, regionType
    

    def map_image(self, quick: bool = False):
        """
        :quick: don't give all the info
        Warning! This function may change
        because warapi is very inconsistent.
        I could not find a more efficient
        way to create an entire map while 
        keeping all of the map markers.
        warapi does not give a sorted list
        of hex names, so i had to put them 
        individually
        """
        
        startTime = time()
        hexImages = [
            [
                self.hex_to_image('BasinSionnachHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 0
                )
            ],
            [
                self.hex_to_image('ReachingTrailHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 1,
                )
            ],
            [
                self.hex_to_image('CallahansPassageHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                self.hex_to_image('DeadLandsHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                self.hex_to_image('UmbralWildwoodHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],
            [
                self.hex_to_image('GreatMarchHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 5,
                )
            ],
            [
                self.hex_to_image('KalokaiHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 6,
                )
            ],
            [
                self.hex_to_image('SpeakingWoodsHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 0.5,
                )
            ],
            [
                self.hex_to_image('MooringCountyHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                self.hex_to_image('LinnMercyHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                self.hex_to_image('LochMorHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                self.hex_to_image('HeartlandsHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                self.hex_to_image('RedRiverHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 5.5,
                )
            ],
            [
                self.hex_to_image('CallumsCapeHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 1,
                )
            ],
            [
                self.hex_to_image('StonecradleHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                self.hex_to_image('KingsCageHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                self.hex_to_image('SableportHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],
            [
                self.hex_to_image('AshFieldsHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 5,
                )
            ],
            [
                self.hex_to_image('NevishLineHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                self.hex_to_image('FarranacCoastHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                self.hex_to_image('WestgateHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                self.hex_to_image('OriginHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                self.hex_to_image('OarbreakerHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -3,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                self.hex_to_image('FishermansRowHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -3,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                self.hex_to_image('StemaLandingHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * -3,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],

            [
                self.hex_to_image('HowlCountyHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 0.5,
                )
            ],
            [
                self.hex_to_image('ViperPitHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                self.hex_to_image('MarbanHollow', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                self.hex_to_image('DrownedValeHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                self.hex_to_image('ShackledChasmHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                self.hex_to_image('AcrithiaHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 5.5,
                )
            ],
            [
                self.hex_to_image('ClansheadValleyHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 1,
                )
            ],
            [
                self.hex_to_image('WeatheredExpanseHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                self.hex_to_image('ClahstraHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                self.hex_to_image('AllodsBightHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],
            [
                self.hex_to_image('TerminusHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 5,
                )
            ],
            [
                self.hex_to_image('MorgensCrossingHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                self.hex_to_image('StlicanShelfHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                self.hex_to_image('EndlessShoreHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                self.hex_to_image('ReaversPassHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                self.hex_to_image('GodcroftsHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 3,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                self.hex_to_image('TempestIslandHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 3,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                self.hex_to_image('TheFingersHex', True, quick),
                (
                    FoxholeAPI.HEX_SIZE[0] * 3,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],
        ]

        totalEnlistments = 0
        totalColonialCasualties = 0
        totalWardenCasualties = 0
        totalCasualties = 0
        
        mapImage = Image.new('RGBA', (FoxholeAPI.HEX_SIZE[0] * 7, FoxholeAPI.HEX_SIZE[1] * 7))
        for hexImageData in hexImages:
            totalEnlistments += hexImageData[0][1]
            totalColonialCasualties += hexImageData[0][2]
            totalWardenCasualties += hexImageData[0][3]
            totalCasualties += hexImageData[0][2] + hexImageData[0][3]
            y = int(hexImageData[1][1])
            position = (int(hexImageData[1][0] + (FoxholeAPI.HEX_SIZE[0] * 7 / 2) - FoxholeAPI.HEX_SIZE[0] * 0.5), y)
            mapImage.alpha_composite(hexImageData[0][0], position)

        backgroundImage = Image.new("RGB", mapImage.size, (43, 45, 49))
        backgroundImage.paste(mapImage, mask=mapImage.split()[3])

        pathId = random.randint(10000000, 99999999)
        backgroundImage.save(f'temp/{pathId}.jpg', 'JPEG', quality=90)

        return pathId, totalEnlistments, totalColonialCasualties, totalWardenCasualties, totalCasualties
    
