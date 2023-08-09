import discord


async def get_or_fetch_message_from_reference(
    message: discord.Message,
) -> discord.Message:
    return message.reference.cached_message or await message.channel.fetch_message(
        message.reference.message_id
    )
