from importlib.resources import path
import pathlib,json,urllib.request,re
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
    if match.is_not_from_this_bot():
        for server in servers:
            if server.room == room.room_id:
                if server.Region == None:
                    server.Region = await getRegionCode(message.body)
                    if server.Region == None:
                        await bot.api.send_text_message(server.room,'Ort wurde nicht gefunden !')
                    else:
                        await save_servers()
@bot.listener.on_custom_event
async def join(room, event):
    pass
async def getRegionCode(plz):
    regFile = pathlib.Path('region_codes.json')
    if not regFile.exists():
        with urllib.request.urlopen('https://www.xrepository.de/api/xrepository/urn:de:bund:destatis:bevoelkerungsstatistik:schluessel:rs_2021-07-31/download/Regionalschl_ssel_2021-07-31.json') as h:
            cont = json.loads(h.read())
            with open(str(regFile),'w') as f:
                json.dump(cont,f)
    else:
        with open(str(regFile),'r') as f:
            cont = json.load(f)
    js = cont['daten']
    for rec in js:
        if plz in rec[1]:
            return rec[0][:6]+'000000'
    return None
def extract_id(post):
    res = None
    if 'alt="id@' in str(post):
        res = post[post.find('alt="id@')+8:]
        res = res[:res.find('"')]
    return res
async def post_html_entry(server,html_body,sender):
    global servers
    mcontent={
        "msgtype": "m.text",#or m.notice seems to be shown more transparent
        "body": re.sub('<[^<]+?>', '', html_body),
        "format": "org.matrix.custom.html",
        "formatted_body": sender+'<br>'+html_body
        }
    await bot.api.async_client.room_send(room_id=server.room,
                                          message_type="m.room.message",
                                          content=mcontent)
async def check_server(server):
    global lastsend,servers
    n: Nina = Nina()
    if not hasattr(server,'Region'):
        await bot.api.send_text_message(server.room,'Für welchen Ort möchten Sie gewarnet werden ?')
        server.Region = None
    if not hasattr(server,'LastId'):
        server.LastId = None
    while True:
        if server.Region:
            n.addRegion(server.Region)
            try:
                await n.update()
                events = await get_room_events(bot.api.async_client,server.room,500)
                for msg in n.warnings[server.Region]:
                    if msg.isValid():
                        for event in events:
                            nLastId = None
                            if hasattr(event,'formatted_body'):
                                nLastId = extract_id(event.formatted_body)
                                if nLastId != msg.id:
                                    nLastId = None
                                else: break
                        if not nLastId:                        
                            sender = '<a href=\"%s\">%s</a><font size="-1"> %s</font>&nbsp;<a href=\"%s\" alt="id@%s" style="display: none">🌐</a>' % ('','NINA','','',msg.id)
                            await post_html_entry(server,msg.headline+'<br>'+msg.description,sender)
                            print(msg)
            except ApiError as error:
                await bot.api.send_text_message(server.room,str(error))
            except BaseException as e:
                if 'Connection' in str(e): pass
                else:
                    await bot.api.send_text_message(server.room,str(e))
        await asyncio.sleep(60*5)
try:
    with open('data.json', 'r') as f:
        nservers = json.load(f)
        for server in nservers:
            servers.append(Server(server))
except BaseException as e: 
    logging.warning('Failed to read data.json:'+str(e))
@bot.listener.on_startup
async def startup(room):
    global loop,servers
    found = False
    loop = asyncio.get_running_loop()
    for server in servers:
        if server.room == room:
            loop.create_task(check_server(server))
            found=True
    if not found:
        server = Server(room=room)
        loop.create_task(check_server(server))
        servers.append(server)
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