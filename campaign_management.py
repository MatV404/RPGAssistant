import discord
from enum import Enum
from typing import Union, List, Tuple


class ChannelType(Enum):
    TEXT = 1
    VOICE = 2


CanRead = bool
CanWrite = bool
Channels = List[Tuple[str, ChannelType, CanRead, CanWrite]]

CAMPAIGN_CHANNELS: Channels = [("campaign-chronicle", ChannelType.TEXT, True, False),
                               ("campaign-general", ChannelType.TEXT, True, True),
                               ("reactions", ChannelType.TEXT, True, True),
                               ("dm-notes", ChannelType.TEXT, False, False),
                               ("bot-commands", ChannelType.TEXT, False, False),
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


async def create_campaign(message: discord.Message, campaign_name) -> None:
    """Creates the category and all chat channels for a D&D Campaign.
    The message author is then promoted to the Campaign's Dungeon Master Role."""
    await message.channel.send(f"Creating {campaign_name} for {message.author.name}. Please wait until "
                               f"an error or success message is returned.")

    # ToDo: Fix typing here.
    server = message.guild
    if server is None:
        await message.channel.send("Error while trying to create the campaign category.")
        return

    new_category = await server.create_category(campaign_name)

    await new_category.set_permissions(server.default_role, view_channel=False)
    await new_category.set_permissions(server.default_role, read_messages=False)

    player_role = await server.create_role(name=f"{campaign_name} Player", permissions=PLAYER_PERMS)
    dm_role = await server.create_role(name=f"{campaign_name} Dungeon Master", permissions=DM_PERMS)

    for name, channel_type, player_read, player_write in CAMPAIGN_CHANNELS:
        if channel_type == ChannelType.TEXT:
            await make_text_channel(server, name, new_category, player_role, dm_role, player_write, player_read)
        else:
            await make_voice_channel(server, name, new_category, player_role, dm_role)

    await message.author.add_roles(dm_role)
    await message.channel.send(f"The campaign {campaign_name} was successfully created!")


async def delete_campaign(message: discord.Message, campaign_name: str) -> None:
    """Deletes the given campaign category, along with all the channels and roles."""
    await message.channel.send(f"Attempting to delete {campaign_name}. Please wait until "
                               f"an error or success message is returned.")
    category = discord.utils.get(message.guild.categories, name=campaign_name)
    if category is None:
        await message.channel.send(f"No campaign by the name of {campaign_name} exists, "
                                   f"did you write the name correctly?")
        return None

    player_role = discord.utils.get(message.guild.roles, name=f"{campaign_name} Player")
    dm_role = discord.utils.get(message.guild.roles, name=f"{campaign_name} Dungeon Master")
    # ToDo: Decide if this should stop the deletion or simply ignore the deletion of the roles.
    if player_role is None or dm_role is None:
        await message.channel.send(f"The {campaign_name} Player role or {campaign_name} Dungeon Master "
                                   f"role does not exist.")
        return None

    for text_channel in category.text_channels:
        await text_channel.delete()
    for voice_channel in category.voice_channels:
        await voice_channel.delete()

    # ToDo: Think about adding try ... except to blocks similar to these. ^ Also deals with that.
    await category.delete()
    await player_role.delete()
    await dm_role.delete()
    # Using author.send in case the author decided to delete the channel they were in. Could probably check for it.
    await message.author.send(f"Campaign {campaign_name} deleted successfully!")


async def rename_campaign(message: discord.Message, campaign_name: str, new_name: str) -> None:
    """Renames the given campaign category and its roles."""
    await message.channel.send(f"Attempting to rename {campaign_name} into {new_name}, please wait until an error "
                               f"or success message is returned.")
    server = message.guild

    if server is None:
        await message.channel.send("Something went wrong while trying to rename the campaign category.")
        return None

    campaign_category = discord.utils.get(server.channels, name=campaign_name)
    if campaign_category is None:
        await message.channel.send(f"A campaign category by the name of {campaign_name} was not found.")
        return None

    player_role = discord.utils.get(server.roles, name=f"{campaign_name} Player")
    dungeon_master_role = discord.utils.get(server.roles, name=f"{campaign_name} Dungeon Master")

    if player_role is None or dungeon_master_role is None:
        await message.channel.send(f"A Player or Dungeon Master role for {campaign_name} does not exist.")
        return None

    await campaign_category.edit(name=new_name)
    await player_role.edit(name=f"{new_name} Player")
    await dungeon_master_role.edit(name=f"{new_name} Dungeon Master")

    await message.channel.send(f"{campaign_name} was successfully renamed to {new_name}.")
