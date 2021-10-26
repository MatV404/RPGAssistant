import discord
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv
import campaign_management
import player_management
import role_management

# ToDo: Think about separating this code for better readability.

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.all()
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix='R!', intents=intents)


async def validate_role(message: discord.Message, role_name: str) -> bool:
    """Used to validate whether a user has the required role in the case of campaign creation / moderation."""
    # Todo: Make this smarter.
    for role in message.author.roles:
        if role.name == role_name:
            return True
    await message.channel.send(f"You do not have the {role_name} role required for this command.")
    return False


async def is_name_unique(message: discord.Message, channel_name: str) -> bool:
    return discord.utils.get(message.guild.categories, name=channel_name) is None


@bot.command()
async def create_campaign(message: discord.Message, campaign_name: str) -> None:
    """Creates the category and all chat channels for a D&D Campaign.
    The message author is then promoted to the Campaign's Dungeon Master Role."""
    if not await validate_role(message, "Dungeon Master") or not await is_name_unique(message, campaign_name):
        return None

    await campaign_management.create(message, campaign_name)


@bot.command()
async def delete_campaign(message: discord.Message, campaign_name: str) -> None:
    """Deletes the given campaign category, along with all the channels and roles."""
    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    await campaign_management.delete(message, campaign_name)


@bot.command()
async def rename_campaign(message: discord.Message, campaign_name: str, new_name: str) -> None:
    if not await validate_role(message, f"{campaign_name} Dungeon Master") \
            or not await is_name_unique(message, new_name):
        return None

    await campaign_management.rename(message, campaign_name, new_name)


@bot.command()
async def add_player(message: discord.Message, campaign_name: str, player_name: str) -> None:
    """Adds a player into the given campaign."""
    server = message.guild
    if server is None:
        await message.channel.send(f"Something went wrong while trying to add the player. :/")
        return None

    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    await player_management.add_to_campaign(server, campaign_name, player_name, message.channel)


@bot.command()
async def remove_player(message: discord.Message, campaign_name: str, player_name: str) -> None:
    """Removes a given player from the campaign."""
    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    server = message.guild
    if server is None:
        await message.channel.send(f"Something went wrong while trying to remove the player. :/")
        return None

    await player_management.remove_from_campaign(server, campaign_name, player_name, message.channel)


@bot.command()
async def set_role_colour(message: discord.Message, role: discord.Role, new_colour_str: str):
    if not await validate_role(message, "Dungeon Master"):
        return None

    # ToDo: Rethink this. Don't like this.
    try:
        new_colour = int(new_colour_str, 16)
    except:
        await message.channel.send("Invalid color code! Remember to use a hex color code without the leading #.")
        return None

    colour = discord.Colour(new_colour)

    await role_management.set_colour(role, colour)


@bot.command()
async def commands(message: discord.Message) -> None:
    # ToDo: Look into embeds to make this message look amazing. Right now it's quite meh.
    await message.channel.send("Here are all my commands!\n"
                               "Please note that if you want to use a campaign name that is more than two words,"
                               "you need to use quotes (\"\") around it."
                               "\n~> `R!create_campaign` \"<Campaign Name>\" => Creates a new Campaign Category for your"
                               "D&D campaign!"
                               "\n~> `R!delete_campaign` \"<Campaign Name>\" => Deletes the given Campaign Category."
                               "\n~> `R!rename_campaign` \"<Campaign Name>\" \"<New Name>\" => Renames the given "
                               "Campaign Category and its roles."
                               "\n~> `R!add_player` \"<Campaign Name>\" <DiscordUser#Number> => Adds a Player to your "
                               "Campaign."
                               "\n~> `R!remove_player` \"<Campaign Name>\" <DiscordUser#Number> "
                               "=> Removes a Player from your Campaign."
                               "\n~> `R!set_role_colour @<role> <hex_code> => Sets the mentioned role's colour to "
                               "<hex code>, be sure to leave out the leading # before the hex code!")


@bot.event
async def on_ready() -> None:
    print(f"Bot connected and ready for work!")


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.id == bot.user.id:
        return None
    await bot.process_commands(message)

bot.run(TOKEN)
