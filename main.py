import discord
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv
from campaign_management import create_campaign, delete_campaign, rename_campaign
from player_management import bulk_add_players, bulk_remove_players
from role_management import set_role_colour

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.all()
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix='R!', intents=intents)


async def validate_role(message: discord.Message, role_name: str) -> bool:
    """Used to validate whether a user has the required role in the case of campaign creation / moderation."""
    # Todo: Make this smarter -> Perhaps implement a database to correlate campaign_name with role_name.
    for role in message.author.roles:
        if role.name == role_name:
            return True
    await message.channel.send(f"You do not have the {role_name} role required for this command.")
    return False


async def is_name_unique(message: discord.Message, channel_name: str) -> bool:
    return discord.utils.get(message.guild.categories, name=channel_name) is None


@bot.command()
async def campaign_create(message: discord.Message, campaign_name: str) -> None:
    """Creates the category and all chat channels for a D&D Campaign.
    The message author is then promoted to the Campaign's Dungeon Master Role."""
    if not await validate_role(message, "Dungeon Master") or not await is_name_unique(message, campaign_name):
        return None

    await create_campaign(message, campaign_name)


@bot.command()
async def campaign_delete(message: discord.Message, campaign_name: str) -> None:
    """Deletes the given campaign category, along with all the channels and roles."""
    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    await delete_campaign(message, campaign_name)


@bot.command()
async def campaign_rename(message: discord.Message, campaign_name: str, new_name: str) -> None:
    """Renames the given campaign category, along with all the roles."""
    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    if not await is_name_unique(message, new_name):
        await message.channel.send(f"Error: A category named {new_name} already exists.")
        return None

    await rename_campaign(message, campaign_name, new_name)


@bot.command()
async def player_add(message: discord.Message, campaign_name: str, *player_names: str) -> None:
    """Adds a player into the given campaign."""
    server = message.guild
    if server is None:
        await message.channel.send(f"Something went wrong while trying to add the player. :/")
        return None

    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    await bulk_add_players(server, campaign_name, player_names, message.channel)


@bot.command()
async def player_remove(message: discord.Message, campaign_name: str, *player_names: str) -> None:
    """Removes a given player from the campaign."""
    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    server = message.guild
    if server is None:
        await message.channel.send(f"Something went wrong while trying to remove the player. :/")
        return None

    await bulk_remove_players(server, campaign_name, player_names, message.channel)


@bot.command()
async def role_colour(message: discord.Message, role: discord.Role, new_colour_str: str):
    """Sets the given role's colour to new_colour"""
    if not await validate_role(message, "Dungeon Master"):
        return None

    # ToDo: Rethink this.
    try:
        new_colour = int(new_colour_str, 16)
    except ValueError:
        await message.channel.send("Invalid color code! Remember to use a hex color code without the leading #.")
        return None

    colour = discord.Colour(new_colour)

    await set_role_colour(role, colour)


@bot.command()
async def commands(message: discord.Message) -> None:
    # ToDo: Fix the Emoji, it doesn't get the proper emoji. :( -> utils.get only gets custom emoji
    emoji = "♦"
    embedded_message = discord.Embed(
        title="RPG Assistant's Command List",
        description="Here are all the commands available for RPG Assistant.",
        colour=discord.Colour.dark_red())
    embedded_message.add_field(name=f"{emoji} R!campaign_create \"<Campaign Name>\"",
                               value="Creates a new campaign category for your D&D campaign, complete "
                                     "with Player and DM roles as well as all necessary channels.",
                               inline=False)

    embedded_message.add_field(name=f"{emoji} R!campaign_delete \"<Campaign Name>\"",
                               value="Deletes a given campaign category, all of its channels, as well as the Player "
                                     "and DM roles.",
                               inline=False)

    embedded_message.add_field(name=f"{emoji} R!campaign_rename \"<Campaign Name>\" \"<New Name>\"",
                               value="Renames the given Campaign Category and its Player and DM roles accordingly.",
                               inline=False)

    embedded_message.add_field(name=f"{emoji} R!player_add \"<Campaign Name>\" <DiscordUser#Number>",
                               value="Adds a player to your campaign, creating their log channel as well. "
                                     "Will add more players if you input more <DiscordUser#Number> values.",
                               inline=False)

    embedded_message.add_field(name=f"{emoji} R!player_remove \"<Campaign Name>\" <DiscordUser#Number>",
                               value="Removes a player from your campaign, deleting their log channel as well. "
                                     "Will remove more players if you input more <DiscordUser#Number> values.",
                               inline=False)

    embedded_message.add_field(name=f"{emoji} R!role_colour @<role> <hex_code>",
                               value="Sets the mentioned role's colour to <hex code>, be sure to leave out the "
                                     "leading # before the hex code!",
                               inline=False)

    embedded_message.add_field(name=f"{emoji} R!commands",
                               value="Displays this useful message!",
                               inline=False)

    embedded_message.set_footer(text="And more to come.")

    await message.channel.send(embed=embedded_message)


@bot.event
async def on_ready() -> None:
    print(f"Bot connected and ready for work!")


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.id == bot.user.id:
        return None
    await bot.process_commands(message)


bot.run(TOKEN)
