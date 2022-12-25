import discord
import requests
import time
import sqlite3

database = False

conn = sqlite3.connect('storage.db')
conn.row_factory = lambda cursor, row: row[0]
c = conn.cursor()

try:
    c.execute("""CREATE TABLE storage (
    name text,
    timeWiped real,
    timeSinceLastWipe real,
    durationLastWipe real
    )""")
except Exception:
    print('database already exists')


timeLastRefresh = 0

def run_discord_bot():
    TOKEN = ''
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    #functions for the database
    def readTimeWiped(guild):
        with conn:
            c.execute("SELECT timeWiped FROM storage WHERE name=:name", {'name':guild})
            return c.fetchall()

    def readTimeSinceLastWipe(guild):
        with conn:
            c.execute("SELECT timeSinceLastWipe FROM storage WHERE name=:name", {'name':guild})
            c.fetchall()

    def readDurationLastWipe(guild):
        with conn:
            c.execute("SELECT durationLastWipe FROM storage WHERE name=:name", {'name':guild})
            c.fetchall()

    def UpdateGuildTimeWiped(guild, timewiped):
        with conn:
            c.execute("UPDATE storage SET timeWiped=:tw WHERE name=:name", {'name': guild,'tw': timewiped,})

    def UpdateGuildTimeLastWipe(guild,timelastwiped):
        with conn:
            c.execute("UPDATE storage SET timeSinceLastWipe=:tslw WHERE name=:name", {'name': guild, 'tslw':timelastwiped,})
    
    def UpdateGuildDurationLastWipe(guild, durationlastwipe):
        with conn:
            c.execute("UPDATE storage SET durationLastWipe=:dlw WHERE name=:name", {'name': guild, 'dlw':durationlastwipe})

    def addGuild(guild,timewiped,timelastwiped,durationlastwipe):
        with conn:
            c.execute("INSERT INTO storage VALUES (:name, :tw, :tslw, :dlw)", {'name': guild,
                                                                                'tw': timewiped,
                                                                                'tslw': timelastwiped,
                                                                                'dlw': durationlastwipe})

    def readAllGuilds():
     with conn:
        c.execute("SELECT name FROM storage")
        return c.fetchall()

    @client.event
    async def on_ready():
        print(f'{client.user} is now running')

    def updateWipedDictTimes():
        for i in readAllGuilds():
            guild = i
            r = requests.get('https://api.wynncraft.com/public_api.php?action=guildStats&command=' + (guild))
            guildterrs = r.json()
            if guildterrs['territories'] == 0:
                tw = time.time_ns()
                UpdateGuildTimeWiped(guild, tw)
            if guildterrs['territories'] > 0:
                x = readTimeWiped(guild)
                dlw = (time.time_ns() - x[0]) / 60000000000
                tw = 0
                tslw = time.time_ns() / 60000000000
                UpdateGuildTimeWiped(guild, tw)
                UpdateGuildDurationLastWipe(guild, dlw)
                UpdateGuildTimeLastWipe(guild, tslw)

    def updateWipedDictGuilds():
        r = requests.get('https://api.wynncraft.com/public_api.php?action=territoryList')
        data = r.json()
        for key in data['territories'].keys():
            name = data['territories'][key]['guild']
            if name in readAllGuilds():
                continue
            else:
                addGuild(name, 0, 0, 0)

    def refreshData():
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
        global timeLastRefresh      
        if time.time() > timeLastRefresh + 300:
            timeLastRefresh = time.time() 
            refreshData()

        if command == 'wiped'or command == 'w':
            
            timeWiped = ''
            if guild in readAllGuilds():
                x = readTimeWiped(guild)
                x = x[0]
                print(x)
                if x != 0:
                    timeWiped = ((time.time_ns() / 60000000000 ) - x)
                    await message.channel.send('time ' + guild +' has been wiped: ' + str(timeWiped) + ' minutes')
                else:
                    r = requests.get('https://api.wynncraft.com/public_api.php?action=guildStats&command=' + (guild))
                    data = r.json()
                    terrs = data['territories']
                    await message.channel.send(guild + ' currently owns ' + str(terrs) + ' territories on the map')
            else:
                await message.channel.send(guild + ' has not owned a territory on the map since the bot has been launched')
        if command == 'lastwiped' or command == 'lw':
            if guild in readAllGuilds():
                #tslw = readTimeSinceLastWipe(guild)
                #tlsw = tslw[0]
                if x != 0:
                    timeSinceLastWipe = x
                    await message.channel.send(guild + ' has been wiped ' + str(timeSinceLastWipe) + ' minutes ago' )
                else:
                    await message.channel.send(guild + ' has never been wiped since gaining a territory')
            else:
                await message.channel.send(guild + ' has not owned a territory on the map since the bot has been launched')
        if command == 'durationlastwipe' or command == 'dlw':
            if guild in readAllGuilds():
                dlw = readDurationLastWipe(guild)
                dlw = dlw[0]
                print(readDurationLastWipe(guild))
                if dlw != 0:
                    await message.channel.send('the last time ' + guild + ' was wiped, it took them ' + str(dlw) + ' minutes to regain a territory')
                else: 
                    await message.channel.send(guild + ' has never been wiped since gaining a territory or is currently wiped')
            else:
                await message.channel.send(guild + ' has not owned a territory on the map since the bot has been launched')




    client.run(TOKEN)




