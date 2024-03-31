import requests
import random
from pprint import pprint

from PIL import Image

from static.items import ITEMS


class FoxholeAPI:
    """ 
    Accurate to 30/03/24
    https://github.com/clapfoot/warapi/tree/master
    """

    WORLD_EXTENT_MINIMUM = (-109199.999997, -94499.99999580906968410989)
    WORLD_EXTENT_MAXIMUM = (109199.999997, 94499.99999580906968410989)
    API_URL = 'https://war-service-live-2.foxholeservices.com/api' # Shard option
    HEX_SIZE = (1024, 888)
    COLONIALS = 'COLONIALS'
    WARDENS = 'WARDENS'
    NONE = 'NONE'


    def war() -> requests.Response:
        return requests.get(FoxholeAPI.API_URL + '/worldconquest/war')
    

    def maps() -> requests.Response:
        return requests.get(FoxholeAPI.API_URL + '/worldconquest/maps')
    

    def map(name: str) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL + f'/worldconquest/warReport/{name}')
    

    def map_static(name: str) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL + f'/worldconquest/maps/{name}/static')


    def map_dynamic(name: str) -> requests.Response:
        return requests.get(FoxholeAPI.API_URL + f'/worldconquest/maps/{name}/dynamic/public')
    

    def debug_all(name: str = None) -> None:
        """
        Get all info from api
        Used by me to debug
        """

        r = FoxholeAPI.war()
        pprint('WAR ' + str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        r = FoxholeAPI.maps()
        pprint('MAPS ' +str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        if not name:
            return
        
        r = FoxholeAPI.map(name)
        pprint('MAP ' +str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        r = FoxholeAPI.map_static(name)
        pprint('STATIC ' +str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        r = FoxholeAPI.map_dynamic(name)
        pprint('DYNAMIC ' +str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())


    def hex_to_image(name: str, isImage: bool = False):
        """
        Returns unique path id of the image
        """

        mapGeneralData = FoxholeAPI.map(name).json()
        mapStaticData = FoxholeAPI.map_static(name).json()
        mapDynamicData = FoxholeAPI.map_dynamic(name).json()

        mapPath = 'static/Images/Maps/Map' + name + '.TGA'

        hexImage = Image.open(
            fp=mapPath
        ).convert('RGBA')

        basesCount = 0
        hasColonialBases = False
        hasWardenBases = False

        for item in mapDynamicData['mapItems']:

            position = (
                FoxholeAPI.HEX_SIZE[0] * item['x'],
                FoxholeAPI.HEX_SIZE[1] * item['y']
            )

            found = False

            for key, value in ITEMS.items():
                if value == item['iconType']:
                    
                    if 'base' in key.lower():
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

                    found = True
                    mapIconPath = 'static/Images/MapIcons/MapIcon' + key + '.TGA'
                
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

            if not found:
                raise Exception('[ERROR] could not find image for an item', item)

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
        elif basesCount < 5:
            color = FoxholeAPI.WARDENS
            if hasColonialBases and isImage:
                hexImage = Image.merge('RGBA', (R.point(lambda p: p  - 132), G.point(lambda p: p  - 81), B.point(lambda p: p  - 32), A))
            else:
                regionType = 'Wardens\' controlled territory'
                hexImage = Image.merge('RGBA', (R.point(lambda p: p  - 88), G.point(lambda p: p  - 54), B.point(lambda p: p  - 21), A))

        if basesCount > 5 and hasWardenBases:
            regionType = 'frontline mostly controlled by Colonials'
        if basesCount < 5 and hasColonialBases:
            regionType = 'frontline mostly controlled by Wardens'

        else:
            ...

        if isImage:
            return hexImage, mapGeneralData['totalEnlistments'], mapGeneralData['colonialCasualties'], mapGeneralData['wardenCasualties']

        pathId = random.randint(10000000, 99999999)
        hexImage.save(f'temp/{pathId}.png')

        return pathId, color, regionType
    

    def map_image():
        """
        Warning! This function may change
        because warapi is very inconsistent.
        I could not find a more efficient
        way to create an entire map while 
        keeping all of the map markers.
        warapi does not give a sorted list
        of hex names, so i had to put them 
        individually
        """

        hexImages = [
            [
                FoxholeAPI.hex_to_image('BasinSionnachHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 0
                )
            ],
            [
                FoxholeAPI.hex_to_image('ReachingTrailHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 1,
                )
            ],
            [
                FoxholeAPI.hex_to_image('CallahansPassageHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                FoxholeAPI.hex_to_image('DeadLandsHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                FoxholeAPI.hex_to_image('UmbralWildwoodHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],
            [
                FoxholeAPI.hex_to_image('GreatMarchHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('KalokaiHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0,
                    FoxholeAPI.HEX_SIZE[1] * 6,
                )
            ],
            [
                FoxholeAPI.hex_to_image('SpeakingWoodsHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 0.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('MooringCountyHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('LinnMercyHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('LochMorHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('HeartlandsHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('RedRiverHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -0.75,
                    FoxholeAPI.HEX_SIZE[1] * 5.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('CallumsCapeHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 1,
                )
            ],
            [
                FoxholeAPI.hex_to_image('StonecradleHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                FoxholeAPI.hex_to_image('KingsCageHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                FoxholeAPI.hex_to_image('SableportHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],
            [
                FoxholeAPI.hex_to_image('AshFieldsHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -1.5,
                    FoxholeAPI.HEX_SIZE[1] * 5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('NevishLineHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('FarranacCoastHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('WestgateHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('OriginHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -2.25,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('OarbreakerHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -3,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                FoxholeAPI.hex_to_image('FishermansRowHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -3,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                FoxholeAPI.hex_to_image('StemaLandingHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * -3,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],

            [
                FoxholeAPI.hex_to_image('HowlCountyHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 0.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('ViperPitHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('MarbanHollow', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('DrownedValeHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('ShackledChasmHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('AcrithiaHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 0.75,
                    FoxholeAPI.HEX_SIZE[1] * 5.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('ClansheadValleyHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 1,
                )
            ],
            [
                FoxholeAPI.hex_to_image('WeatheredExpanseHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                FoxholeAPI.hex_to_image('ClahstraHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                FoxholeAPI.hex_to_image('AllodsBightHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 4,
                )
            ],
            [
                FoxholeAPI.hex_to_image('TerminusHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 1.5,
                    FoxholeAPI.HEX_SIZE[1] * 5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('MorgensCrossingHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 1.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('StlicanShelfHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 2.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('EndlessShoreHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 3.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('ReaversPassHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 2.25,
                    FoxholeAPI.HEX_SIZE[1] * 4.5,
                )
            ],
            [
                FoxholeAPI.hex_to_image('GodcroftsHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 3,
                    FoxholeAPI.HEX_SIZE[1] * 2,
                )
            ],
            [
                FoxholeAPI.hex_to_image('TempestIslandHex', True),
                (
                    FoxholeAPI.HEX_SIZE[0] * 3,
                    FoxholeAPI.HEX_SIZE[1] * 3,
                )
            ],
            [
                FoxholeAPI.hex_to_image('TheFingersHex', True),
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
        for i, hexImageData in enumerate(hexImages):
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
        backgroundImage.save(f'temp/{pathId}.jpg', 'JPEG', quality=60)

        return pathId, totalEnlistments, totalColonialCasualties, totalWardenCasualties, totalCasualties
    