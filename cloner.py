import discord
from discord.ext import commands
import aiohttp

TOKEN = "Enter Your Token"
SOURCE_GUILD_ID = "srv id you want to copy"
TARGET_GUILD_ID = "Target srv id"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", self_bot=True, intents=intents)

@bot.command()
async def sync(ctx):
    if ctx.guild.id != int(TARGET_GUILD_ID):
        await ctx.send("This command can only be used in the target server.")
        return

    source_guild = bot.get_guild(int(SOURCE_GUILD_ID))
    target_guild = ctx.guild

    if not source_guild:
        await ctx.send("Source guild not found.")
        return

    roles = [r for r in source_guild.roles if not r.is_default()]
    for role in sorted(roles, key=lambda r: r.position):
        if discord.utils.get(target_guild.roles, name=role.name):
            continue
        try:
            new_role = await target_guild.create_role(
                name=role.name,
                permissions=role.permissions,
                colour=role.colour,
                hoist=role.hoist,
                mentionable=role.mentionable
            )
            await ctx.send(f"Created role: {role.name}")
        except Exception as e:
            await ctx.send(f"Failed to create role {role.name}: {e}")

    role_map = {r.name: discord.utils.get(target_guild.roles, name=r.name) for r in roles}

    category_map = {}
    for category in sorted(source_guild.categories, key=lambda c: c.position):
        overwrites = {}
        for target, overwrite in category.overwrites.items():
            if isinstance(target, discord.Role):
                new_role = role_map.get(target.name)
                if new_role:
                    overwrites[new_role] = overwrite
        try:
            new_cat = await target_guild.create_category(
                name=category.name,
                overwrites=overwrites,
                position=category.position
            )
            category_map[category.id] = new_cat
            await ctx.send(f"Created category: {category.name}")
        except Exception as e:
            await ctx.send(f"Failed to create category {category.name}: {e}")

    for channel in sorted(source_guild.text_channels, key=lambda c: c.position):
        overwrites = {}
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Role):
                new_role = role_map.get(target.name)
                if new_role:
                    overwrites[new_role] = overwrite
        new_cat = category_map.get(channel.category_id)
        try:
            new_ch = await target_guild.create_text_channel(
                name=channel.name,
                overwrites=overwrites,
                topic=channel.topic,
                nsfw=channel.nsfw,
                slowmode_delay=channel.slowmode_delay,
                category=new_cat,
                position=channel.position
            )
            await ctx.send(f"Created text channel: {channel.name}")
        except Exception as e:
            await ctx.send(f"Failed to create text channel {channel.name}: {e}")

    for channel in sorted(source_guild.voice_channels, key=lambda c: c.position):
        overwrites = {}
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Role):
                new_role = role_map.get(target.name)
                if new_role:
                    overwrites[new_role] = overwrite
        new_cat = category_map.get(channel.category_id)
        try:
            new_ch = await target_guild.create_voice_channel(
                name=channel.name,
                overwrites=overwrites,
                bitrate=channel.bitrate,
                user_limit=channel.user_limit,
                category=new_cat,
                position=channel.position
            )
            await ctx.send(f"Created voice channel: {channel.name}")
        except Exception as e:
            await ctx.send(f"Failed to create voice channel {channel.name}: {e}")

    async with aiohttp.ClientSession() as session:
        for emoji in source_guild.emojis:
            try:
                async with session.get(str(emoji.url)) as resp:
                    img_bytes = await resp.read()
                await target_guild.create_custom_emoji(name=emoji.name, image=img_bytes)
                await ctx.send(f"Created emoji: {emoji.name}")
            except Exception as e:
                await ctx.send(f"Failed to create emoji {emoji.name}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN, bot=False)
