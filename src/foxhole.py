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
    API_URL = 'https://war-service-live-2.foxholeservices.com/api'
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
        pprint(str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        r = FoxholeAPI.maps()
        pprint(str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        if not name:
            return
        
        r = FoxholeAPI.map(name)
        pprint(str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        r = FoxholeAPI.map_static(name)
        pprint(str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())

        r = FoxholeAPI.map_dynamic(name)
        pprint(str(r.status_code) + ' ::: ' + str(r.headers))
        pprint(r.json())


    def hex_to_image(name: str) -> str:
        """
        Returns unique path id of the image
        """

        mapStaticData = FoxholeAPI.map_static(name).json()
        mapDynamicData = FoxholeAPI.map_dynamic(name).json()

        mapPath = 'static/Images/Maps/Map' + name + '.TGA'

        hex = Image.open(
            fp=mapPath
        ).convert('RGBA')

        for item in mapDynamicData['mapItems']:

            position = (
                FoxholeAPI.HEX_SIZE[0] * item['x'],
                FoxholeAPI.HEX_SIZE[1] * item['y']
            )

            found = False

            for key, value in ITEMS.items():

                if value == item['iconType']:

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
                    hex.alpha_composite(itemImage, position)

            if not found:
                raise Exception('[ERROR] could not find image for an item', item)

        pathId = random.randint(10000000, 99999999)
        hex.save(f'temp/{pathId}.png')

        return pathId
    