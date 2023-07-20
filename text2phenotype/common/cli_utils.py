from argparse import ArgumentParser


class CommonCLIArguments:
    def __init__(self):
        self.parser = ArgumentParser()
        self.parser.add_argument('--debug', dest='debug', action='store_true',
                                 default=False, help='run service in debug mode')

    @property
    def args(self):
        return self.parser.parse_args()

    @property
    def debug(self):
        return self.args.debug
