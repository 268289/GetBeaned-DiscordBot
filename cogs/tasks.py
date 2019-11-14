import collections
import json
import time

import discord
from discord.ext import tasks, commands
from typing import Dict

from cogs.helpers import checks
from cogs.helpers.actions import full_process, unban, unmute
from cogs.helpers.helpful_classes import LikeUser


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.run_tasks.start()
        self.tasks_mapping = {
            "refresh_user": self.refresh_user,
            "unmute": self.unmute_task,
            "unban": self.unban_task,
        }

    def cog_unload(self):
        self.run_tasks.stop()

    async def unmute_task(self, task):
        arguments = json.loads(task['arguments']) # {"target": 514557845111570447, "guild": 512328935304855555, "reason": "Time is up (1 week, 2 days and 23 hours)"}
        guild_id = arguments["guild"]

        guild:discord.Guild = self.bot.get_guild(guild_id)

        if guild:
            member = guild.get_member(arguments["target"])
            if member:
                tasks_user = LikeUser(did=5, name="DoItLater", guild=guild)
                act = await full_process(self.bot, unmute, member, tasks_user, arguments["reason"], automod_logs=f"Task number #{task['id']}")
                return True

    async def unban_task(self, task):
        arguments = json.loads(task['arguments'])  # {"target": 514557845111570447, "guild": 512328935304855555, "reason": "Time is up (1 week, 2 days and 23 hours)"}
        guild_id = arguments["guild"]

        guild: discord.Guild = self.bot.get_guild(guild_id)

        if guild:
            member = guild.get_member(arguments["target"])
            if member:
                tasks_user = LikeUser(did=5, name="DoItLater", guild=guild)
                act = await full_process(self.bot, unban, member, tasks_user, arguments["reason"], automod_logs=f"Task number #{task['id']}")
                return True

        # Failed because no such guild/user

    async def refresh_user(self, task):
        user = self.bot.get_user(int(task["arguments"]))

        if user is None:
            user = await self.bot.fetch_user(int(task["arguments"]))

        if user:
            await self.bot.api.add_user(user)
            return True
        else:
            return False

    async def dispatch_task(self, task):
        self.bot.logger.info(f"Running task #{task['id']}")
        self.bot.logger.debug(str(task))

        task_type = task["type"]

        try:
            res = await self.tasks_mapping[task_type](task)
            if res is not False:  # So if res is None, it'll still return True
                return True
        except KeyError:
            self.bot.logger.warning(f"Unsupported task #{task['id']}, type is {task['type']}")
            return False  # Unsupported task type

    @tasks.loop(minutes=1)
    async def run_tasks(self):
        #self.bot.logger.info("Cleaning up cache")
        tasks = await self.bot.api.get_tasks()
        for task in tasks:
            res = await self.dispatch_task(task)

            if res:
                self.bot.logger.info(f"Completed task #{task['id']}")
                await self.bot.api.complete_task(task["id"])

    @run_tasks.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("We are running tasks.")


def setup(bot):
    tasks = Tasks(bot)
    bot.add_cog(tasks)