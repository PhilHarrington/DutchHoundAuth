from discord.ext import commands
import discord
import asyncio
from os.path import isfile
import json
import string
import random
import sys
import datetime
import time

bot = commands.Bot(command_prefix='!', description='Simple authorization bot by KrykiZZ#1111')


def check_config():
    return isfile('settings.json')


def get_codes():
    with open('codes.txt', 'r') as codes_file:
        return codes_file.read().split('\n')


def get_settings():
    with open('settings.json', 'r') as settings_file:
        return json.load(settings_file)


def write_codes(codes):
    with open('codes.txt', 'r+') as codes_file:
        codes_file.seek(0)
        for code in codes:
            codes_file.write(f'{code}\n')
        codes_file.truncate()


def write_settings(settings):
    with open('settings.json', 'r+') as settings_file:
        settings_file.seek(0)
        json.dump(settings, settings_file)
        settings_file.truncate()


@bot.event
async def on_ready():
    print(f'Logged in {bot.user.name} on {len(bot.servers)} servers.')


@bot.command(pass_context=True)
async def ping(ctx: discord.ext.commands.Context):
    await bot.say('pong')


@bot.command(pass_context=True)
async def activate(ctx: discord.ext.commands.Context, code: str = None):
    if code is None or not isinstance(code, str):
        await bot.say('Unknown code format.')
    else:
        settings = get_settings()
        codes = get_codes()
        if code in codes:
            # Add role
            server = bot.get_server(settings['bot']['server_id'])
            role = discord.utils.get(server.roles, id=settings['bot']['role_id'])
            member = server.get_member(ctx.message.author.id)

            try:
                await bot.add_roles(member, role)
            except discord.ext.commands.errors.CommandInvokeError:
                print('Missing permissions for adding role.')

            # Remove used code
            codes.pop(codes.index(code))
            write_codes(codes)

            # Add member to settings
            settings['members'][member.id] = str(datetime.datetime.now().timestamp())
            write_settings(settings)

            embed = discord.Embed(color=53380,
                                  description='Welcome to the Project SNKRFY! Thank you for supporting us!')
            embed.set_author(name='Success',
                             icon_url='http://allsorce.com/wp-content/uploads/2018/08/21213/1200x630bb.jpg')
            t = time.strftime("%c", time.gmtime((datetime.datetime.now() + datetime.timedelta(days=30)).timestamp()))
            embed.add_field(
                name='Membership ends in',
                value=t, inline=True)
            await bot.say(embed=embed)
            print(f'Member [{member.id}]{member.name}#{member.discriminator} activated code {code}')
        else:
            embed = discord.Embed(
                title='The key you have entered is invalid or it is already in use! Double check it!',
                color=12530000)
            embed.set_author(name='Error!', icon_url='https://wallscover.com/images/errors-2.jpg')
            await bot.say(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if message.server is None and not message.author.bot:
        if message.content.replace(bot.command_prefix, '').split()[0] in bot.commands:
            await bot.process_commands(message)
        else:
            await bot.send_message(message.author, 'I am only a bot. Send me your license key to get membership!')


async def check_task():
    await bot.wait_until_ready()
    while not bot.is_closed:
        with open('settings.json', 'r+') as settings_file:
            settings = json.load(settings_file)
            try:
                for member in settings['members']:
                    member_date = datetime.datetime.fromtimestamp(round(float(settings['members'][member])))
                    delta = datetime.datetime.now()-member_date
                    if delta.days > 30:
                        server = bot.get_server(settings['bot']['server_id'])
                        role = discord.utils.get(server.roles, id=settings['bot']['role_id'])
                        d_member = server.get_member(member)
                        await bot.remove_roles(d_member, role)
                        del settings['members'][member]
                        settings_file.seek(0)
                        json.dump(settings, settings_file)
                        settings_file.truncate()

                        embed = discord.Embed(color=12926976, title='Unfortunately, your membership has been expired !')
                        embed.set_author(name='Warning!', icon_url='https://wallscover.com/images/errors-2.jpg')
                        await bot.send_message(d_member, embed=embed)
                        print(f'[{d_member.id}]{d_member.name}#{d_member.discriminator} key expired.')
            except RuntimeError:
                # idk why
                pass
        await asyncio.sleep(5)


# Ярик, заводи ебучий трактор, и погнали хуярить!
async def connect(token: str):
    while not bot.is_closed:
        print('Connecting...')
        try:
            await bot.start(token)
        except Exception as e:
            print('Bot disconnected Discord.' + str(e.__dict__))
            await asyncio.sleep(5)

if __name__ == "__main__":
    if check_config():
        with open('settings.json') as settings_file:
            bot.loop.create_task(check_task())
            bot.loop.run_until_complete(connect(json.load(settings_file)['bot']['token']))
    else:
        print('Config file not found. Please check settings.json file and configure it.')
        default_config = {
          "bot": {
            "token": ""
          }
        }
        with open('settings.json', 'w') as outfile:
            json.dump(default_config, outfile)
        sys.exit()
