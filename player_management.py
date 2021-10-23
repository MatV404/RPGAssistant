import discord
from typing import Union


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


async def add_to_campaign(server: discord.Guild, campaign_name: str, player_name: str,
                          channel: Union[discord.VoiceChannel, discord.TextChannel]) -> None:
    await channel.send(f"Adding {player_name} to {campaign_name}.")

    player_role = discord.utils.get(server.roles, name=f"{campaign_name} Player")
    dm_role = discord.utils.get(server.roles, name=f"{campaign_name} Dungeon Master")

    if dm_role is None or player_role is None:
        await channel.send("Error: No DM or Player Role for the given Campaign Exists!")
        return None

    name_parts = player_name.split("#")
    if len(name_parts) != 2:
        await channel.send(f"Please, ensure the player's name is in a format of NAME#NUMBER.")
        return None

    player = discord.utils.get(server.members, name=name_parts[0], discriminator=name_parts[1])
    if player is None:
        await channel.send(f"Error: No player called {player_name} found!")
        return None

    await channel.send("Creating the player's log channel.")
    if not await create_player_channel(server, campaign_name, player, dm_role):
        await channel.send("Something went wrong while creating the player channel.")
        return None

    player.add_roles(player_role)
    await channel.send("Player added successfully!")


async def delete_player_channel(server: discord.Guild, campaign_name: str, player_name: str) -> bool:
    """Deletes a given campaign player's log channel."""
    current_category = discord.utils.get(server.categories, name=campaign_name)
    channel_to_delete = discord.utils.get(current_category.channels, name=f"{player_name.lower()}-log")

    if current_category is None or channel_to_delete is None:
        return False

    await channel_to_delete.delete()
    return True


async def remove_from_campaign(server: discord.Guild, campaign_name: str, player_name: str,
                               channel: Union[discord.VoiceChannel, discord.TextChannel]) -> None:
    await channel.send(f"Removing {player_name} from {campaign_name}.")

    name_parts = player_name.split("#")
    if len(name_parts) != 2:
        await channel.send(f"Please, ensure the player's name is in a format of NAME#NUMBER.")
        return None

    player = discord.utils.get(server.members, name=name_parts[0], discriminator=name_parts[1])
    if player is None:
        await channel.send(f"Error: No player called {player_name} found!")
        return None

    player_role = discord.utils.get(player.roles, name=f"{campaign_name} Player")
    if player_role is None:
        await channel.send(f"Error: The player doesn't have the required {campaign_name} Player role.")
        return None

    if not await delete_player_channel(server, campaign_name, player.name):
        await channel.send(f"Error: The Category {campaign_name} or "
                                   f"Log Channel {player_name.lower()}-log do not exist.")
        return None

    await player.remove_roles(player_role)

    await channel.send(f"Player {player_name} successfully removed from {campaign_name}.")