import discord


async def set_role_colour(role: discord.Role, new_colour: discord.Colour) -> None:
    """Sets the colour for a specific server role."""
    await role.edit(colour=new_colour)
    return None


async def send_role_dm(role: discord.Role, message: str) -> None:
    """Sends a message to all users for a specific role. Use with caution!"""
    for user in role.members:
        print(f"Sending to {user.name}")
        await user.send(message)
