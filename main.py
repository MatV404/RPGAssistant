import discord
from discord.ext import commands
from typing import Union, Optional
from os import getenv
from enum import Enum
from dotenv import load_dotenv

# ToDo: Think about separating this code for better readability.

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.all()
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix='R!', intents=intents)


class ChannelType(Enum):
    TEXT = 1
    VOICE = 2


CanRead = bool
CanWrite = bool
Channels = list[tuple[str, ChannelType, CanRead, CanWrite]]

CAMPAIGN_CHANNELS: Channels = [("campaign-chronicle", ChannelType.TEXT, True, False),
                               ("campaign-general", ChannelType.TEXT, True, True),
                               ("reactions", ChannelType.TEXT, True, True),
                               ("dm-notes", ChannelType.TEXT, False, False),
                               ("session-voice", ChannelType.VOICE, True, True),
                               ("other-voice", ChannelType.VOICE, True, True)]

PLAYER_PERMS = discord.Permissions(read_messages=True,
                                   send_messages=True,
                                   connect=True,
                                   use_external_emojis=True,
                                   change_nickname=True,
                                   speak=True,
                                   stream=True,
                                   embed_links=True,
                                   attach_files=True,
                                   add_reactions=True)

DM_PERMS = discord.Permissions(read_messages=True,
                               send_messages=True,
                               mention_everyone=True,
                               connect=True,
                               use_external_emojis=True,
                               change_nickname=True,
                               speak=True,
                               stream=True,
                               embed_links=True,
                               attach_files=True,
                               add_reactions=True,
                               priority_speaker=True,
                               mute_members=True,
                               move_members=True,
                               deafen_members=True)


async def validate_role(message: discord.Message, role_name: str) -> bool:
    """Used to validate whether a user has the required role in the case of campaign creation / moderation."""
    # Todo: Make this smarter.
    for role in message.author.roles:
        if role.name == role_name:
            return True
    await message.channel.send(f"You do not have the {role_name} role required for this command.")
    return False


async def set_role_perms(channel: Union[discord.TextChannel, discord.VoiceChannel],
                         permissions_role: discord.Role, is_voice: bool,
                         send_privilege: bool, read_privilege: bool) -> None:
    """An auxiliary function that handles the assignment of permissions to a role in the given channel."""
    await channel.set_permissions(permissions_role,
                                  overwrite=None)
    if not is_voice:
        await channel.set_permissions(permissions_role,
                                      view_channel=True,
                                      read_message_history=True,
                                      send_messages=send_privilege,
                                      read_messages=read_privilege)
    else:
        await channel.set_permissions(permissions_role,
                                      view_channel=True,
                                      connect=True,
                                      speak=True,
                                      stream=True)


async def make_text_channel(server: discord.Guild, name: str,
                            parent_category: discord.CategoryChannel,
                            player_role: discord.Role,
                            dungeon_master_role: discord.Role,
                            player_write: bool, player_read: bool):
    """Creates a Discord Text Channel, setting permissions for the player and dungeon master roles accordingly."""
    channel = await server.create_text_channel(name, overwrites=None)
    await channel.edit(category=parent_category)
    await channel.edit(sync_permissions=True)

    await set_role_perms(channel, player_role, False, player_write, player_read)
    await set_role_perms(channel, dungeon_master_role, False, True, True)


async def make_voice_channel(server, name: str,
                             parent_category: discord.CategoryChannel,
                             player_role: discord.Role,
                             dungeon_master_role: discord.Role):
    """Creates a Discord Voice Channel, setting permissions for the player and dungeon master roles accordingly."""
    channel = await server.create_voice_channel(name, overwrites=None)
    await channel.edit(category=parent_category)
    await channel.edit(sync_permissions=True)

    await set_role_perms(channel, player_role, True, False, False)
    await set_role_perms(channel, dungeon_master_role, True, False, False)


async def is_name_unique(message: discord.Message, channel_name: str) -> bool:
    return discord.utils.get(message.guild.categories, name=channel_name) is None


@bot.command()
async def create_campaign(message, campaign_name) -> None:
    """Creates the category and all chat channels for a D&D Campaign.
    The message author is then promoted to the Campaign's Dungeon Master Role."""
    if not await validate_role(message, "Dungeon Master") or not await is_name_unique(message, campaign_name):
        return None

    await message.channel.send(f"Creating {campaign_name} for {message.author.name}.")
    # ToDo: Fix typing here.

    server: Optional[discord.Guild] = message.guild
    if server is None:
        await message.channel.send("Error while trying to create the campaign category.")
        return

    await message.channel.send(f"Creating {campaign_name} Category.")
    new_category = await server.create_category(campaign_name)

    await new_category.set_permissions(server.default_role, view_channel=False)
    await new_category.set_permissions(server.default_role, read_messages=False)

    await message.channel.send(f"Creating {campaign_name} player and dungeon master roles.")
    player_role = await server.create_role(name=f"{campaign_name} Player", permissions=PLAYER_PERMS)
    dm_role = await server.create_role(name=f"{campaign_name} Dungeon Master", permissions=DM_PERMS)

    await message.channel.send(f"Creating {campaign_name} channels.")
    for name, channel_type, player_read, player_write in CAMPAIGN_CHANNELS:
        if channel_type == ChannelType.TEXT:
            await make_text_channel(server, name, new_category, player_role, dm_role, player_write, player_read)
        else:
            await make_voice_channel(server, name, new_category, player_role, dm_role)

    await message.author.add_roles(dm_role)
    await message.channel.send(f"The campaign {campaign_name} was successfully created!")


@bot.command()
async def delete_campaign(message: discord.Message, campaign_name: str) -> None:
    """Deletes the given campaign category, along with all the channels and roles."""
    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    category = discord.utils.get(message.guild.categories, name=campaign_name)
    if category is None:
        await message.channel.send(f"No campaign by the name of {campaign_name} exists, "
                                   f"did you write the name correctly?")
        return None

    await message.channel.send("Deleting text channels.")
    for text_channel in category.text_channels:
        await text_channel.delete()

    await message.channel.send("Deleting voice channels.")
    for voice_channel in category.voice_channels:
        await voice_channel.delete()

    player_role = discord.utils.get(message.guild.roles, name=f"{campaign_name} Player")
    dm_role = discord.utils.get(message.guild.roles, name=f"{campaign_name} Dungeon Master")

    await message.channel.send("Deleting the category.")
    await category.delete()
    await message.channel.send("Deleting player and dungeon master roles.")
    await player_role.delete()
    await dm_role.delete()
    await message.channel.send(f"Campaign {campaign_name} deleted successfully!")


async def create_player_channel(server: discord.Guild, parent_category: str,
                                member: discord.User, dm_role: discord.Role) -> bool:
    """Creates a log channel for the given campaign player."""
    current_category = discord.utils.get(server.categories, name=parent_category)
    if current_category is None:
        return False

    # ToDo: Refactor this line to not be as long.
    channel = await server.create_text_channel(f"{member.name} log",
                                               overwrites={server.default_role: discord.PermissionOverwrite(view_channel=False)})
    await channel.edit(category=current_category)

    channel.overwrites_for(member)
    await channel.set_permissions(member,
                                  view_channel=True,
                                  read_message_history=True,
                                  send_messages=True,
                                  read_messages=True)

    channel.overwrites_for(dm_role)
    await channel.set_permissions(dm_role,
                                  view_channel=True,
                                  read_message_history=True,
                                  send_messages=True,
                                  read_messages=True)
    return True


async def get_roles(message: discord.Message,
                    category_name: str) -> tuple[Optional[discord.Role], [Optional[discord.Role]]]:
    """Retrieves the Player and Dungeon Master Roles for a given category name."""
    dm_role = discord.utils.get(message.guild.roles, name=f"{category_name} Dungeon Master")
    player_role = discord.utils.get(message.guild.roles, name=f"{category_name} Player")

    return dm_role, player_role


@bot.command()
async def add_player(message: discord.Message, campaign_name: str, player_name: str) -> None:
    """Adds a player into the given campaign."""
    server = message.guild
    if server is None:
        await message.channel.send(f"Something went wrong while trying to add the player. :/")
        return None
    # ToDo: Fix the typing issues with server
    assert server is not None

    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    await message.channel.send(f"Adding {player_name} to {campaign_name}.")
    dm_role, player_role = await get_roles(message, campaign_name)

    if dm_role is None or player_role is None:
        await message.channel.send("Error: No DM or Player Role for the given Campaign Exists!")
        return None

    name_parts = player_name.split("#")
    if len(name_parts) == 1:
        await message.channel.send(f"Please, ensure the player's name is in a format of NAME#NUMBER.")
        return None

    player = discord.utils.get(server.members, name=name_parts[0], discriminator=name_parts[1])
    if player is None:
        await message.channel.send(f"Error: No player called {player_name} found!")
        return None

    await message.channel.send("Creating the player's log channel.")
    if not await create_player_channel(server, campaign_name, player, dm_role):
        await message.channel.send("Something went wrong while creating the player channel.")
        return None

    await message.channel.send("Player added successfully!")


async def delete_player_channel(server: discord.Guild, campaign_name: str, player_name: str) -> bool:
    """Deletes a given campaign player's log channel."""
    current_category = discord.utils.get(server.categories, name=campaign_name)
    channel_to_delete = discord.utils.get(current_category, name=f"{player_name.lower()}-log")

    if current_category is None or channel_to_delete is None:
        return False

    await channel_to_delete.delete()
    return True


@bot.command()
async def remove_player(message: discord.Message, campaign_name: str, player_name: str) -> None:
    """Removes a given player from the campaign."""
    if not await validate_role(message, f"{campaign_name} Dungeon Master"):
        return None

    await message.channel.send(f"Removing {player_name} from {campaign_name}.")

    name_parts = player_name.split("#")
    if len(name_parts) == 1:
        await message.channel.send(f"Please, ensure the player's name is in a format of NAME#NUMBER.")
        return None

    server = message.guild
    if server is None:
        await message.channel.send(f"Something went wrong while trying to remove the player. :/")
        return None
    # ToDo: Figure out the typing for this poor boy.
    assert server is not None

    player = discord.utils.get(message.guild.members, name=name_parts[0], discriminator=name_parts[1])
    if player is None:
        await message.channel.send(f"Error: No player called {player_name} found!")
        return None

    player_role = discord.utils.get(player.roles, name=f"{campaign_name} Player")
    if player_role is None:
        await message.channel.send(f"Error: The player doesn't have the required {campaign_name} Player role.")
        return None

    await player.remove_roles(player_role)

    if not await delete_player_channel(server, campaign_name, player.name):
        await message.channel.send(f"Error: The Category {campaign_name} or "
                                   f"Log Channel {player_name.lower()}-log do not exist.")
        return None

    await message.channel.send(f"Player {player_name} successfully removed from {campaign_name}.")


@bot.command()
async def commands(message: discord.Message) -> None:
    # ToDo: Look into embeds to make this message look amazing. Right now it's quite meh.
    await message.channel.send("Here are all my commands!"
                               "\n+ `R!create_campaign` <Campaign Name> => Creates a new Campaign Category for your"
                               "D&D campaign!"
                               "\n+ `R!delete_campaign` <Campaign Name> => Deletes the given Campaign Category."
                               "\n+ `R!add_player` <Campaign Name> <DiscordUser#Number> => Adds a Player to your "
                               "Campaign."
                               "\n+ `R!remove_player` <Campaign Name> <DiscordUser#Number> "
                               "=> Removes a Player from your Campaign.")


@bot.event
async def on_ready() -> None:
    print(f"Bot connected and ready for work!")


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.id == bot.user.id:
        return None
    await bot.process_commands(message)

bot.run(TOKEN)
