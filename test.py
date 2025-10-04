from functions import config
from javascript import require, On

mineflayer = require('mineflayer')

login_config = {
  'host': config.MINECRAFT_HOST,
  'port': config.MINECRAFT_PORT,
  'username': config.MINECRAFT_USERNAME,
  'version':'1.21.4'
}
if config.MINECRAFT_AUTH:
  login_config['auth'] = 'microsoft'
bot = mineflayer.createBot(login_config)

print("Started mineflayer")

@On(bot, 'spawn')
def handle(*args):
  print("I spawned")


@On(bot, "login")
def login(this):
    bot.chat("Hi everyone!")


@On(bot, "spawn")
def spawn(this):
    bot.chat("I spawned, watch out!")


@On(bot, "spawnReset")
def spawnReset(this, message):
    bot.chat("Oh noez! My bed is broken.")


@On(bot, "forcedMove")
def forcedMove(this):
    p = bot.entity.position
    bot.chat(f"I have been forced to move to {p.toString()}")


@On(bot, "health")
def health(this):
    bot.chat(f"I have {bot.health} health and {bot.food} food")


@On(bot, "death")
def death(this):
    bot.chat("I died x.x")


@On(bot, "kicked")
def kicked(this, reason, *a):
    print("I was kicked", reason, a)
    console.log(f"I got kicked for {reason}")


@On(bot, "time")
def time(this):
    bot.chat(f"Current time: " + str(bot.time.timeOfDay))


@On(bot, "rain")
def rain(this):
    if bot.isRaining:
        bot.chat("It started raining")
    else:
        bot.chat("It stopped raining")


@On(bot, "noteHeard")
def noteHeard(this, block, instrument, pitch):
    bot.chat(f"Music for my ears! I just heard a {instrument.name}")


@On(bot, "chestLidMove")
def chestLidMove(this, block, isOpen, *a):
    action = "open" if isOpen else "close"
    bot.chat(f"Hey, did someone just {action} a chest?")


@On(bot, "pistonMove")
def pistonMove(this, block, isPulling, direction):
    action = "pulling" if isPulling else "pushing"
    bot.chat(f"A piston is {action} near me, i can hear it.")


@On(bot, "playerJoined")
def playerJoined(this, player):
    print("joined", player)
    if player["username"] != bot.username:
        bot.chat(f"Hello, {player['username']}! Welcome to the server.")


@On(bot, "playerLeft")
def playerLeft(this, player):
    if player["username"] == bot.username:
        return
    bot.chat(f"Bye ${player.username}")


@On(bot, "playerCollect")
def playerCollect(this, collector, collected):
    if collector.type == "player" and collected.type == "object":
        raw_item = collected.metadata[10]
        item = Item.fromNotch(raw_item)
        header = ("I'm so jealous. " + collector.username) if (
            collector.username != bot.username) else "I "
        bot.chat(f"{header} collected {item.count} {item.displayName}")


@On(bot, "entitySpawn")
def entitySpawn(this, entity):
    if entity.type == "mob":
        p = entity.position
        console.log(f"Look out! A {entity.displayName} spawned at {p.toString()}")
    elif entity.type == "player":
        bot.chat(f"Look who decided to show up: {entity.username}")
    elif entity.type == "object":
        p = entity.position
        console.log(f"There's a {entity.displayName} at {p.toString()}")
    elif entity.type == "global":
        bot.chat("Ooh lightning!")
    elif entity.type == "orb":
        bot.chat("Gimme dat exp orb!")


@On(bot, "entityHurt")
def entityHurt(this, entity):
    if entity.type == "mob":
        bot.chat(f"Haha! The ${entity.displayName} got hurt!")
    elif entity.type == "player":
        if entity.username in bot.players:
            ping = bot.players[entity.username].ping
            bot.chat(f"Aww, poor {entity.username} got hurt. Maybe you shouldn't have a ping of {ping}")


@On(bot, "entitySwingArm")
def entitySwingArm(this, entity):
    bot.chat(f"{entity.username}, I see that your arm is working fine.")


@On(bot, "entityCrouch")
def entityCrouch(this, entity):
    bot.chat(f"${entity.username}: you so sneaky.")


@On(bot, "entityUncrouch")
def entityUncrouch(this, entity):
    bot.chat(f"{entity.username}: welcome back from the land of hunchbacks.")


@On(bot, "entitySleep")
def entitySleep(this, entity):
    bot.chat(f"Good night, {entity.username}")


@On(bot, "entityWake")
def entityWake(this, entity):
    bot.chat(f"Top of the morning, {entity.username}")


@On(bot, "entityEat")
def entityEat(this, entity):
    bot.chat(f"{entity.username}: OM NOM NOM NOMONOM. That's what you sound like.")


@On(bot, "entityAttach")
def entityAttach(this, entity, vehicle):
    if entity.type == "player" and vehicle.type == "object":
        print(f"Sweet, {entity.username} is riding that {vehicle.displayName}")


@On(bot, "entityDetach")
def entityDetach(this, entity, vehicle):
    if entity.type == "player" and vehicle.type == "object":
        print(f"Lame, {entity.username} stopped riding the {vehicle.displayName}")


@On(bot, "entityEquipmentChange")
def entityEquipmentChange(this, entity):
    print("entityEquipmentChange", entity)


@On(bot, "entityEffect")
def entityEffect(this, entity, effect):
    print("entityEffect", entity, effect)


@On(bot, "entityEffectEnd")
def entityEffectEnd(this, entity, effect):
    print("entityEffectEnd", entity, effect)