import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import ollama
from ollama import chat
import aiohttp
import aiofiles

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
client = ollama.Client()
model = os.getenv('MODEL')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents=discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('bot is ready')

@bot.event
async def on_presence_update(before, after):
    if before.status in [discord.Status.offline, discord.Status.invisible] and after.status == discord.Status.online:
        # print(f'{after.name} is now online')
        channel = bot.get_channel(1467117943459545193)
        await channel.send(f'{after.name} is now online!')

@bot.command()
async def m(ctx, *, message):
    has_image = False
    image_path = None

    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                has_image = True
                image_path = f'temp_{attachment.filename}'
                await attachment.save(image_path)
                break

    if not has_image:
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
        words = message.split()
        for word in words:
            if word.startswith('http') and any(word.lower().endswith(ext) for ext in image_extensions):
                has_image = True
                image_path = f'temp_image{os.path.splitext(word)[1]}'
                async with aiohttp.ClientSession() as session:
                    async with session.get(word) as resp:
                        if resp.status == 200:
                            async with aiofiles.open(image_path, 'wb') as f:
                                await f.write(await resp.read())
                break

    if has_image:
        try:
            response = chat(model=model, messages=[{'role': 'user', 'content': message, 'images': [image_path]}])
            await ctx.send(response['message']['content'])
        finally:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
    else:
        response = client.generate(model=model, prompt=message)
        await ctx.send(response.response)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)