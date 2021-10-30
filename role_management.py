import discord


async def set_role_colour(role: discord.Role, new_colour: discord.Colour) -> None:
    """Sets the colour for a specific server role."""
    await role.edit(colour=new_colour)
    return None


async def send_role_dm(server: discord.Guild, author: discord.User, role: discord.Role, message: str) -> None:
    """Sends a message to all users for a specific role. Use with caution!"""
    user_message = discord.Embed(
        title=f"❗ New Message for all users with the {role.name} role ❗",
        description=message,
        colour=role.colour)

    user_message.set_footer(text=f"This message was sent by {author.name} from {server.name}.")

    for user in role.members:
        await user.send(embed=user_message)
