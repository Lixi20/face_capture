#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
from os.path import join, dirname
from pathlib import Path

from utils.config_builder import ConfigBuilder
from utils.face_util import interrupt_from_keyboard_handler, FaceCaptureUtils
from utils.face_conf import PrivateConfig, PublicConfig
from happy_python import HappyLog, HappyConfigParser

hlog = HappyLog.get_instance()
config: PublicConfig
private_config: PrivateConfig

__mod_name__ = 'face_capture'
__mod_desc__ = '视频人物面部捕捉'
__config_file_path__ = join(dirname(__file__), 'conf/face_capture.conf')

with open(join(dirname(__file__), 'face_capture_help/version.txt'), encoding='utf-8') as f:
    __version__ = f.read().strip()


def build_help():
    parser = ConfigBuilder.build_help_parser(prog=__mod_name__,
                                             description=__mod_desc__,
                                             version=__version__,
                                             config_file_path=__config_file_path__)

    parser.add_argument('-i',
                        '--input_video_file',
                        help='输入视频文件',
                        type=str,
                        dest='input_video_file',
                        )

    parser.add_argument('-s',
                        '--input_sub_file',
                        help='输入视频字幕文件',
                        type=str,
                        dest='input_video_file',
                        )

    parser.add_argument('-o',
                        '--output_face_img_dir',
                        help='截取面部保存目录',
                        type=str,
                        dest='output_face_img_dir',
                        )

    return parser


def get_face_info():
    avatar_output_path = FaceCaptureUtils.private_config.avatar_output_path
    sub_path = FaceCaptureUtils.private_config.sub_path
    video_path = FaceCaptureUtils.private_config.video_path
    subtitle_times = FaceCaptureUtils.parse_subtitles(str(sub_path))

    face_data = []

    # video_frames_results = FaceCaptureUtils.capture_avatar_from_video(video_path=video_path,
    #                                                                   subtitle_times=subtitle_times,
    #                                                                   avatar_output_path=avatar_output_path,
    #                                                                   frame_redundancy=FaceCaptureUtils.public_config.frame_redundancy,
    #                                                                   target_size=(
    #                                                                   FaceCaptureUtils.public_config.image_width,
    #                                                                   FaceCaptureUtils.public_config.image_height),
    #                                                                   eye_diff_threshold=FaceCaptureUtils.public_config.eye_diff_threshold)

    video_frames_results = FaceCaptureUtils.capture_avatar_from_video(video_path=Path(video_path),
                                                                      subtitle_times=subtitle_times,
                                                                      avatar_output_path=Path(avatar_output_path),
                                                                      frame_redundancy=50,
                                                                      target_size=(
                                                                      300,
                                                                      300),
                                                                      eye_diff_threshold=50)


    hlog.info('video_frames_results->%s', video_frames_results)


def main():
    global config
    global private_config

    parser = build_help()

    args = ConfigBuilder.build_help_with_parser(parser=parser)

    config_builder = ConfigBuilder(mod_config=Path(args.conf_file),
                                   is_dry_run_from_cmd_args=args.dry_run,
                                   is_verbose_from_cmd_args=args.verbose)
    config = config_builder.config

    private_config = PrivateConfig()
    HappyConfigParser.load(args.conf_file, private_config)

    FaceCaptureUtils.init(private_config=private_config)

    get_face_info()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, interrupt_from_keyboard_handler)
    main()
