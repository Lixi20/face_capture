import signal
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from utils.face_util import interrupt_from_keyboard_handler, hlog
from utils.face_conf import PublicConfig
from happy_python import HappyLog, HappyConfigParser


class ConfigBuilder:
    mod_conf: dict[Any, Any]
    parser: ArgumentParser

    def __init__(self, mod_config: Path, is_dry_run_from_cmd_args, is_verbose_from_cmd_args):
        signal.signal(signal.SIGINT, interrupt_from_keyboard_handler)

        if not mod_config.exists():
            hlog.error('配置文件（%s）不存在' % mod_config)
            exit(1)

        self.hlog = HappyLog.get_instance(str(mod_config))

        self.is_dry_run = True if is_dry_run_from_cmd_args else None
        self.is_verbose = True if is_verbose_from_cmd_args else None

        self.config = PublicConfig()
        HappyConfigParser.load(str(mod_config), self.config)

        self.mod_config_path = str(mod_config)

        self._dry_run = self.config.dry_run if self.is_dry_run is None else True

        self._dry_run_convert = True if str(self._dry_run).lower() in ['true', '1', 't', 'y', 'yes', 'yeah'] else False

    @staticmethod
    def build_help_parser(prog: str, description: str, version: str, config_file_path: str) -> ArgumentParser:
        parser = ArgumentParser(prog=prog + ' ' + version, description=description)
        parser.add_argument('-c',
                            '--conf',
                            help='指定配置文件',
                            dest='conf_file',
                            type=str,
                            default=config_file_path)

        parser.add_argument('-n',
                            '--dry-run',
                            help='在不做任何更改的情况下试运行，通常和"-v"参数一起使用',
                            dest='dry_run',
                            action='store_true')

        parser.add_argument('-v',
                            '--verbose',
                            help='显示详细信息',
                            dest='verbose',
                            action='store_true')

        parser.add_argument('-V',
                            '--version',
                            help='显示版本信息',
                            action='version',
                            version='face capture version: %(prog)s/v' + version)

        return parser

    @staticmethod
    def build_help(prog: str, description: str, version: str, mod_config_file_path: str):
        parser = ConfigBuilder.build_help_parser(prog=prog,
                                                 description=description,
                                                 version=version,
                                                 config_file_path=mod_config_file_path,
                                                 )
        return parser.parse_args()

    @staticmethod
    def build_help_with_parser(parser: ArgumentParser):
        return parser.parse_args()
