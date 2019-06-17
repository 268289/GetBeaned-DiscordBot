import asyncio
import time

import discord
from discord import Color
from discord.ext import commands

from cogs.helpers import checks
from cogs.helpers.helpful_classes import LikeUser
from cogs.helpers.level import get_level
from cogs.helpers.actions import full_process, note, warn

import string


class FakeCtx:
    def __init__(self, guild, bot):
        self.guild = guild
        self.bot = bot


class Dehoister(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def dehoist_user_in_guild(self, user, guild) -> bool:
        if await self.bot.settings.get(guild, "dehoist_enable"):
            member = guild.get_member(user.id)

            if await get_level(FakeCtx(guild, self.bot), member) > int(await self.bot.settings.get(guild, "dehoist_ignore_level")):
                return False

            intensity = int(await self.bot.settings.get(guild, "dehoist_intensity"))

            previous_nickname = member.display_name
            new_nickname = previous_nickname

            if intensity >= 1:
                new_nickname = previous_nickname.lstrip("!")

            if intensity >= 2:
                for pos, char in enumerate(new_nickname):
                    if char not in string.ascii_letters:
                        continue
                    else:
                        new_nickname = new_nickname[pos:]
                        break

            if intensity >= 3:
                new_nickname += "zz"

                while new_nickname.lower()[:2] == "aa":
                    new_nickname = new_nickname[2:]

                new_nickname = new_nickname[:-2]

            if previous_nickname != new_nickname:
                if len(new_nickname) == 0:
                    new_nickname = "z_Nickname_DeHoisted"

                reason = f"Automatic nickname DeHoist from {previous_nickname} to {new_nickname}. " \
                         f"Please try not to use special chars at the start of your nickname to appear at the top of the list of members."

                await member.edit(nick=new_nickname, reason=reason)

                actions_to_take = {
                    "note": note,
                    "warn": warn,
                    "message": None,
                    "nothing": None
                }
                action_name = await self.bot.settings.get(guild, "dehoist_action")

                action_coroutine = actions_to_take[action_name]

                if action_coroutine:
                    moderator = LikeUser(did=3, name="DeHoister", guild=guild)
                    await full_process(self.bot, action_coroutine, member, moderator, reason)

                if action_name != "nothing":

                    try:
                        await member.send(f"Your nickname/username was dehoisted on {guild.name}. "
                                          f"Please try not to use special chars at the start of your nickname to appear at the top of the list of members. "
                                          f"Thanks! Your new nickname is now `{new_nickname}`")
                    except discord.Forbidden:
                        pass

                return True
            else:
                return False
        else:
            return False

    async def dehoist_user(self, user):
        for guild in self.bot.guilds:
            if user in guild.members:
                await self.dehoist_user_in_guild(user, guild)

    @commands.command()
    @commands.guild_only()
    @checks.have_required_level(4)
    @checks.bot_have_permissions()
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.guild)
    async def dehoist_users(self, ctx):
        guild = ctx.guild
        dehoisted_users_count = 0

        await ctx.send(f"Processing, please wait.")

        for member in guild.members:
            dehoisted_users_count += int(await self.dehoist_user_in_guild(member, guild))

        await ctx.send(f"{dehoisted_users_count} users were dehoisted.")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            self.bot.logger.info(f"Member {after} changed nick ({before.nick} -> {after.nick}), running dehoister")

            await self.dehoist_user_in_guild(after, after.guild)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.name != after.name:
            self.bot.logger.info(f"User {after} changed name ({before.name} -> {after.name}), running dehoister")

            await self.dehoist_user(after)


def setup(bot):
    bot.add_cog(Dehoister(bot))