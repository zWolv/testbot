import discord
import requests
import time

def run_discord_bot():
    TOKEN = 'NzIzNDczNTg4OTMzNDkyNzM3.G38yhP.wsepP94btK9q6K7FEeWv-sDaSOVYPSO7dpP1UI'
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    @client.event

    async def on_ready():
        print(f'{client.user} is now running')
    
    prefix = '-'
    @client.event
    async def on_message(message):
        if message.author == client or message.content[0:len(prefix)] != prefix:
            return

        notWiped = { }
        wiped = { }
        msg = str(message.content[len(prefix):len(message.content)])
        command = msg.split()[0]
        if command == 'wiped':
            r = requests.get('https://api.wynncraft.com/public_api.php?action=territoryList')
            data = r.json()
            keys = data['territories'].keys()
            for key in keys:
                copy = False
                for x in range(len(notWiped)):
                    if notWiped[x] == data['territories']['guild']:
                        copy = True
                if not copy:
                    notWiped.insert(data['territories']['guild'])
            for x in len(notWiped):
                guild = notWiped[x]
                r2 = requests.get('https://api.wynncraft.com/public_api.php?action=guildStats&command=' + (guild))
                guildterrs = r2.json()
                if guildterrs['territories'] == 0:
                    notWiped.remove(guild)
                    wiped.insert(guild)
                
                #start timer for specific wiped guild



                #check if wiped guild has regained a terr and stop timer, save that time (time since last wipe maybe?)


                #format time to readable time

            await message.channel.send('temp message')

        







    client.run(TOKEN)




