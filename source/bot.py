from importlib.resources import path
import pathlib,json,urllib.request
from init import *
from pynina import Nina, ApiError
loop = None
lastsend = None
class Server(Config):
    def __init__(self, room, **kwargs) -> None:
        super().__init__(room, **kwargs)
@bot.listener.on_message_event
async def tell(room, message):
    global servers,lastsend
    match = botlib.MessageMatch(room, message, bot, prefix)
    for server in servers:
        if server.room == room.room_id:
            if server.Region == None:
                server.Region = getRegionCode(message.)
async def getRegionCode(plz):
    regFile = pathlib.Path('region_codes.json')
    if not regFile.exists():
        with urllib.request.urlopen('https://www.xrepository.de/api/xrepository/urn:de:bund:destatis:bevoelkerungsstatistik:schluessel:rs_2021-07-31/download/Regionalschl_ssel_2021-07-31.json') as h:
            cont = h.read()
            with open(str(regFile),'w') as f:
                f.write(cont)
    else:
        with open(str(regFile),'r') as f:
            cont = f.read()
    js = json.loads(cont)
async def check_server(server):
    global lastsend,servers
    n: Nina = Nina()
    if not hasattr(server,'Region'):
        await bot.api.send_text_message(server.room,'Für welche Postleitzahl möchten Sie gewarnet werden ?')
        server.Region = None
    while True:
        try:
            await n.update()
            for i in n.warnings["146270000000"]:
                print(i)
                print(i.isValid())
        except ApiError as error:
            await bot.api.send_text_message(server.room,str(error))
        except BaseException as e:
            if 'Connection' in str(e): pass
            else:
                await bot.api.send_text_message(server.room,str(e))
        await asyncio.sleep(15)
try:
    with open('data.json', 'r') as f:
        nservers = json.load(f)
        for server in nservers:
            servers.append(Server(server))
except BaseException as e: 
    logging.warning('Failed to read config.yml:'+str(e))
@bot.listener.on_startup
async def startup(room):
    global loop,servers
    loop = asyncio.get_running_loop()
    for server in servers:
        if server.room == room:
            loop.create_task(check_server(server))
@bot.listener.on_message_event
async def bot_help(room, message):
    bot_help_message = f"""
    Help Message:
        prefix: {prefix}
        commands:
            speaking to bot:
                is used as rcon console command when you are in the admins list
            speaking in channel:
                is send as server global chat message if supported
            listen:
                command: listen server rcon_port [password] [Query Port]
                description: add ark server
            help:
                command: help, ?, h
                description: display help command
                """
    match = botlib.MessageMatch(room, message, bot, prefix)
    if match.is_not_from_this_bot() and match.prefix() and (
       match.command("help") 
    or match.command("?") 
    or match.command("h")):
        await bot.api.send_text_message(room.room_id, bot_help_message)
bot.run()