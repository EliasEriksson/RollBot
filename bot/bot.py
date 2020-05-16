from typing import *
from .errors import *
from .parser import CommandParser
from .manager import Manager
import argparse
import discord
import random
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class Args:
    limit = "limit"
    user = "user"
    amount = "amount"


class Client(discord.Client):
    manager = Manager

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        self.parser = CommandParser()
        subparsers = self.parser.add_subparsers()
        roll_parser = subparsers.add_parser("/roll")
        give_parser = subparsers.add_parser("/give")
        wallet_parser = subparsers.add_parser("/balance")
        register_parser = subparsers.add_parser("/register")

        roll_parser.add_argument(
            Args.limit, nargs="?", type=int, default=100,
            help="The upper limit to roll to.")
        roll_parser.set_defaults(func=self._roll)

        give_parser.add_argument(
            Args.user, type=str,
            help="Discord user @ mention.")
        give_parser.add_argument(
            Args.amount, type=int,
            help="Amount of coins to give to the other user.")
        give_parser.set_defaults(func=self._give)

        wallet_parser.add_argument(
            Args.user, nargs="?", type=str,
            help="Checks the balance of a user.")
        wallet_parser.set_defaults(func=self._balance)

        register_parser.add_argument(
            Args.user, nargs="?", type=str,
            help="Mention of the user to be registered.")
        register_parser.set_defaults(func=self._register)

        self.mention_re_pattern = re.compile(
            r"^<@(\d+)>$")

    @staticmethod
    async def _roll(args: argparse.Namespace, message: discord.Message) -> None:
        limit: int = getattr(args, Args.limit)
        roll = random.randint(1, limit)
        await message.channel.send(f"{message.author.display_name} rolled `{roll}`.")

    async def _register(self, args: argparse.Namespace, message: discord.Message) -> None:
        user_id = self.get_user_id_from_args(args, message.author.id)
        member: discord.Member = message.channel.guild.get_member(user_id)
        try:
            await self.manager.add_user(user_id, 1000)
            await message.channel.send(f"User {member.display_name} registered.")
        except UserAlreadyExists:
            await message.channel.send(f"User {member.display_name} is already registered.")

    async def _balance(self, args: argparse.Namespace, message: discord.Message) -> None:
        user_id = self.get_user_id_from_args(args, message.author.id)
        member: discord.Member = message.guild.get_member(user_id)
        try:
            balance = await self.manager.get_users_wallet(user_id)
            await message.channel.send(f"Balance of {member.display_name}: `{balance}` coins.")
        except UserDoesNotExist:
            message.channel.send(f"User {member.display_name} is not registered.")

    async def _give(self, args: argparse.Namespace, message: discord.Message) -> None:
        match = self.mention_re_pattern.search(getattr(args, Args.user))
        if not match:
            raise InvalidArgument
        sender_id: int = message.author.id
        receiver_id = int(match.groups()[0])
        amount = getattr(args, Args.amount)
        member: discord.Member = message.guild.get_member(receiver_id)
        try:
            await self.manager.give_money(sender_id, receiver_id, amount)
            await message.channel.send(f"Moved `{amount}` from {message.author} to {member.mention}.")
        except SenderDoesNotExist:
            await message.channel.send(f"{message.author.display_name} is not registered.")
        except ReceiverDoesNotExist:
            await message.channel.send(f"{member.display_name} is not registered.")

    async def _provide_welfare(self):
        members: List[int] = []
        for guild in self.guilds:
            guild: discord.Guild
            for member in guild.members:
                member: discord.Member
                voice: discord.VoiceState = member.voice
                status: discord.Status = member.status
                if not voice:
                    continue
                if not status == discord.Status.online:
                    continue
                members.append(member.id)
        await self.manager.add_welfare(*members, amount=11)

    async def _acquire_tax(self):
        members: List[int] = []
        for guild in self.guilds:
            guild: discord.Guild
            for member in guild.members:
                member: discord.Member
                members.append(member.id)
        await self.manager.acquire_tax(*members, tax=0.045)

    async def on_ready(self) -> None:
        self.manager = await Manager.open()
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self._provide_welfare, IntervalTrigger(
            minutes=1, seconds=11))
        scheduler.add_job(self._acquire_tax, CronTrigger(
            hour=0
        ))
        scheduler.start()
        print("Bot now ready.")

    async def on_message(self, message: discord.Message) -> None:
        if not message.author.bot:
            try:
                args = self.parser.parse_args(message.content.split())
                await args.func(args, message)
            except CommandNotImplemented:
                pass

    def get_user_id_from_args(self, args: argparse.Namespace, default=None):
        user_mention = getattr(args, Args.user)
        if user_mention:
            match = self.mention_re_pattern.search(user_mention)
            if match:
                return int(match.groups()[0])
        return default
