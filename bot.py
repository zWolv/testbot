import discord
import requests
import time
import sqlite3
import threading

database = False
conn = sqlite3.connect('storage.db', check_same_thread=False)
conn.row_factory = lambda cursor, row: row[0]
c = conn.cursor()

try:
    c.execute("""CREATE TABLE storage (
    name text,
    timeWiped real,
    durationLastWipe real,
    territories int,
    timesWiped int,
    totalDurationWiped real
    )""")
except Exception:
    print('database already exists')
refreshinterval = 60
call_next = time.time()
previousterr = {}
def run_discord_bot():
    TOKEN = 'NzIzNDczNTg4OTMzNDkyNzM3.Gbqhjq.luvl6e1aJSLG2yOzDh7F2t8ZH5LieMk_7LSIh4'
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    #functions for database 1 (storage)
    def readTimeWiped(guild):
        with conn:
            c.execute("SELECT timeWiped FROM storage WHERE name=:name", {'name':guild})
            return c.fetchall()

    def readDurationLastWipe(guild):
        with conn:
            c.execute("SELECT durationLastWipe FROM storage WHERE name=:name", {'name':guild})
            return c.fetchall()

    def UpdateGuildTimeWiped(guild, timewiped):
        with conn:
            c.execute("UPDATE storage SET timeWiped=:tw WHERE name=:name", {'name': guild,'tw': timewiped,})
    
    def UpdateGuildDurationLastWipe(guild, durationlastwipe):
        with conn:
            c.execute("UPDATE storage SET durationLastWipe=:dlw WHERE name=:name", {'name': guild, 'dlw':durationlastwipe})

    def addGuild(guild,timewiped,durationlastwipe,terrs, wipecount, totalduration):
        with conn:
            c.execute("INSERT INTO storage VALUES (:name, :tw, :dlw, :terrcount, :tws, :tdw)", {'name': guild,
                                                                                'tw': timewiped,
                                                                                'dlw': durationlastwipe,
                                                                                'terrcount': terrs,
                                                                                'tws':wipecount,
                                                                                 'tdw': totalduration})

    def UpdateGuildTerritories(guild, terrs):
        with conn:
            c.execute("UPDATE storage SET territories=:terrcount WHERE name=:name", {'terrcount': terrs, 'name': guild})
            c.fetchall()

    def readGuildTerritories(guild):
        with conn:
            c.execute("SELECT territories FROM storage WHERE name=:name", {'name': guild})
            return c.fetchall()

    def readAllGuilds():
     with conn:
        c.execute("SELECT name FROM storage")
        return c.fetchall()

    def readAverageTimeWiped(guild):
        with conn:
            c.execute("SELECT totalDurationWiped FROM storage WHERE name=:name", {'name': guild})
            x = c.fetchall()
            c.execute("SELECT timesWiped FROM storage WHERE name=:name", {'name': guild})
            y = c.fetchall()
            return x[0] / y[0]

    def readWipeCount(guild):
        with conn:
            c.execute("SELECT timesWiped FROM storage WHERE name=:name", {'name': guild})
            return c.fetchall()

    def updateWipeCount(guild, count):
        with conn:
            c.execute("UPDATE storage SET timesWiped=:wiped WHERE name=:name", {"wiped": count, 'name': guild})
        
    def updateTotalWipeDuration(guild, duration):
        with conn:
            c.execute("UPDATE storage SET totalDurationWiped=:tdw WHERE name=:name", {"tdw": duration, 'name': guild})

    def readTotalDurationWiped(guild):
        with conn:
            c.execute("SELECT totalDurationWiped FROM storage WHERE name=:name", {'name': guild})
            return c.fetchall()

    @client.event
    async def on_ready():
        print(f'{client.user} is now running')
        refreshData()


    def guildWipedAction(guild, terrs): 
        if previousterr[guild] != 0:
            tw = time.time() / 60
            x = readWipeCount(guild)
            x = x[0] + 1
            updateWipeCount(guild, x)
            UpdateGuildTimeWiped(guild, tw)
            UpdateGuildTerritories(guild, terrs)
            previousterr[guild] = terrs

    def guildReturnedAction(guild, terrs):
        x = readTimeWiped(guild)
        y = readTotalDurationWiped(guild)
        y = y[0]
        if previousterr[guild] == 0:
            dlw = (time.time() / 60) - x[0]
        else:
            dlw = readDurationLastWipe(guild)
            dlw = dlw[0]
        tw = 0
        y += dlw
        updateTotalWipeDuration(guild, y)
        UpdateGuildTimeWiped(guild, tw)
        UpdateGuildDurationLastWipe(guild, dlw)
        UpdateGuildTerritories(guild, terrs)
        previousterr[guild] = terrs

    def updateWipedDictTimes():
        for i in readAllGuilds():
            guild = i
            r = requests.get('https://api.wynncraft.com/public_api.php?action=guildStats&command=' + (guild))
            data = r.json()
            guildterrs = data['territories']
            global previousterr
            if guildterrs == 0:
                if guild in previousterr.keys():
                    guildWipedAction(guild, guildterrs)
                else:
                    previousterr[guild] = guildterrs
                    guildWipedAction(guild, guildterrs)
            if guildterrs > 0:
                
                if guild in previousterr.keys():
                    guildReturnedAction(guild, guildterrs)
                else:
                    previousterr[guild] = guildterrs
                    guildReturnedAction(guild, guildterrs)
                    

    def updateWipedDictGuilds():
        r = requests.get('https://api.wynncraft.com/public_api.php?action=territoryList')
        data = r.json()
        for key in data['territories'].keys():
            name = data['territories'][key]['guild']
            if name in readAllGuilds():
                continue
            else:
                addGuild(name, 0, 0, 0, 0, 0)

    def refreshData():
            global refreshinterval
            global call_next
            call_next += refreshinterval
            threading.Timer(call_next - time.time(), refreshData).start()
            updateWipedDictGuilds()
            updateWipedDictTimes()
            print('refreshed data')

    prefix = '-'
    @client.event
    async def on_message(message):
        if message.author == client or message.content[0:len(prefix)] != prefix:
            return

        
        msg = str(message.content[len(prefix):len(message.content)])
        command = msg.split()[0]
        guild = ''
        if len(msg.split()) > 1:
            for x in range(len(msg.split())):
                if x > 0:
                    if x > 1:
                        guild += '_'
                    guild += msg.split()[x]
        global previousterr
        if command == 'wiped'or command == 'w':
            timeWiped = ''
            if guild in readAllGuilds():
                x = readTimeWiped(guild)
                x = x[0]
                y = readWipeCount(guild)
                ls = []
                if x != 0:
                    timeWiped = ((time.time() / 60) - x)
                else:
                    timeWiped = 0
                ls.append(guild)
                ls.append(timeWiped) # does not work properly
                ls.append(y[0])
                ls.append(readAverageTimeWiped(guild))
                await message.channel.send(ls)  
            else:
                await message.channel.send(guild + ' has not owned a territory on the map since the bot has been launched')

        if command == 'addtestguild' or command == 'atg':
            if guild not in readAllGuilds():
                addGuild(guild,0,0,1,0,0)
            await message.channel.send('testguild has been added with 1 territory!')

        if command == 'wipetest' or command == 'wt':
            UpdateGuildTerritories(guild,0)
            previousterr[guild] = 0
            tw = time.time() / 60
            UpdateGuildTimeWiped(guild, tw)
            x = readWipeCount(guild)
            updateWipeCount(guild, x[0] + 1)

        if command == 'unwipe' or command == 'uw':
            UpdateGuildTerritories(guild,1)
            x = readTimeWiped(guild)
            y = readTotalDurationWiped(guild)
            y = y[0]
            if previousterr[guild] == 0:
                dlw = (time.time() / 60) - x[0]
            else:
                dlw = readDurationLastWipe(guild)
                dlw = dlw[0]
            tw = 0
            y += dlw
            UpdateGuildTimeWiped(guild, tw)
            UpdateGuildDurationLastWipe(guild, dlw)
            updateTotalWipeDuration(guild, y)
            

    client.run(TOKEN)




