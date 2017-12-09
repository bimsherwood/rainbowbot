#!/usr/local/bin/python3

import asyncio
#import concurrent.futures
import discord
import getpass
import signal
import logging

# Log everything
logging.basicConfig(level=logging.INFO)

# Params
rainbowRoleName = "Rainbow"

# Account information.
# Passwords are taken at runtime.
email = "bimmosherwood@gmail.com"
targetServersContinuous = [
  "182036599448535040"]
targetServersStepped = [
  "182036599448535040"]

# A discord.Client which rotates a role's colour through the rainbow.
# The best effect is created when any people with that role speak in
# succession.
class RainbowBot(discord.Client):

  ### Events ###

  # Override
  async def on_message(self, msg):
    # For messages in server channels (which have authors with roles)
    if "roles" in msg.author.__dir__():
      await self.increment_rainbow(msg)

  # Override
  @staticmethod
  async def on_ready():
    print("Ready.");

  ### Entry points ###

  async def run(self):
    
    # Initialisations
    self.rainbow_hues = {} # Server ID / hue pairs.
    for serverID in targetServersStepped:
      self.rainbow_hues[serverID] = 0
    for serverID in targetServersContinuous:
      self.rainbow_hues[serverID] = 0
    
    asyncio.ensure_future(self.increment_rainbow_periodic())

    # Log in
    print("Log in to ", email)
    password = getpass.getpass("Password: ")
    print("Logging in to", email + "...")
    await self.login(email, password)
    print("Logged in. Connecting...")
    await self.connect()
  
  ### Utility ###
  
  # Polls the `shuttingDown` semaphore and logs out
  #  (Polling seems to provide better consistency than awaiting a disconnect)
  async def shutdown(self):
    await self.logout()
  
  async def increment_rainbow(self, trigger_message):
    
    # Only do servers in the servers list
    server = trigger_message.server
    if not server.id in targetServersStepped:
      return
    
    # Only do roles authors with a rainbowRoleName role.
    if not rainbowRoleName in map(
        lambda r: r.name,
        trigger_message.author.roles):
      return
    
    for role in server.roles:
      if role.name == rainbowRoleName:
        newColour = discord.Colour(
          value=rainbow(self.rainbow_hues[server.id]))
        self.rainbow_hues[server.id] += 10
        self.rainbow_hues[server.id] %= 360
        await self.edit_role(server, role, colour=newColour)
        break
  
  async def increment_rainbow_periodic(self):
    while True:
      await asyncio.sleep(1)
      for serverId in targetServersContinuous:
        server = self.get_server(serverId)
        if not server:
          break
        for role in server.roles:
          if role.name == rainbowRoleName:
            newColour = discord.Colour(
              value=rainbow(self.rainbow_hues[server.id]))
            self.rainbow_hues[server.id] += 10
            self.rainbow_hues[server.id] %= 360
            await self.edit_role(server, role, colour=newColour)
            break

# Takes hue as degrees, Returns colour code #RRGGBB
# Thanks Wikipedia!
def rainbow(hue):
  hh = hue / 60
  x = 1 - abs(hh % 2 - 1)
  x *= 255
  x = int(x)
  rgb = (0,0,0)
  if hh < 1:
    rgb = (255, x, 0)
  elif hh < 2:
    rgb = (x, 255, 0)
  elif hh < 3:
    rgb = (0, 255, x)
  elif hh < 4:
    rgb = (0, x, 255)
  elif hh < 5:
    rgb = (x, 0, 255)
  else:
    rgb = (255, 0, x)
  return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]

# Get the event loop and create the bot.
loop = asyncio.get_event_loop()
bot = RainbowBot()

# Setup for the Ctrl-C signal.
# First signal schedules graceful shutdown.
# Second signal kills the bot forcefully.
killedOnce = False
def kill_handler(signum, frame):
  global killedOnce
  print("Signalled.")
  if killedOnce:
    loop.stop()
    quit()
  else:
    killedOnce = True
    asyncio.ensure_future(bot.shutdown())
signal.signal(signal.SIGINT, kill_handler)
signal.signal(signal.SIGTERM, kill_handler)

# Run the bot.
try:
  loop.run_until_complete(bot.run())
except KeyboardInterrupt:
  loop.run_until_complete(bot.shutdown())
  print("Logged out.")
finally:
  print("Halting...")
  loop.close()
