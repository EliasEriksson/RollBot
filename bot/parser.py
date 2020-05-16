from .errors import CommandNotImplemented
import argparse


class CommandParser(argparse.ArgumentParser):
    def exit(self, *_):
        pass

    def error(self, *_):
        raise CommandNotImplemented()
