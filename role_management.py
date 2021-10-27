import discord


async def set_role_colour(role: discord.Role, new_colour: discord.Colour) -> None:
    """Sets the colour for a specific server role."""
    await role.edit(colour=new_colour)
    return None
