import re
import av
import cv2

from pathlib import Path
from deepface import DeepFace
from utils.character_Info_enum import GenderType, RaceType, EmotionType
from utils.face_conf import PrivateConfig,PublicConfig

from happy_python import HappyLog

hlog = HappyLog.get_instance()


# noinspection PyUnusedLocal
def interrupt_from_keyboard_handler(signum, frame):
    hlog.warning('检测到用户发送终止信号，退出程序中......')
    exit(1)


class FaceCaptureUtils:
    private_config: PrivateConfig
    public_config: PublicConfig

    @staticmethod
    def init(private_config: PrivateConfig):
        FaceCaptureUtils.private_config = private_config
        FaceCaptureUtils.public_config = PublicConfig

    @staticmethod
    def ensure_directory_exists(directory_path):
        if not Path(directory_path).exists():
            Path(directory_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_max_prediction(predictions):
        """获取概率最高的预测结果"""
        return max(predictions.items(), key=lambda x: x[1])

    @staticmethod
    def get_enum_by_value(enum_class, value):
        """根据值获取对应的枚举类型"""
        try:
            return next(item for item in enum_class if item.value.lower() == value.lower())
        except StopIteration:
            raise ValueError('无效的(%s)枚举值：%s' % (enum_class, value))

    @staticmethod
    def convert_time_to_frames(time_str, fps):
        """将字幕时间字符串 (hh:mm:ss,ms) 转换为对应的视频帧数"""
        time_parts = time_str.split(',')
        seconds = time_parts[0]
        milliseconds = int(time_parts[1])

        h, m, s = map(int, seconds.split(':'))
        total_seconds = h * 3600 + m * 60 + s + milliseconds / 1000
        frame_number = int(total_seconds * fps)
        return frame_number

    @staticmethod
    def parse_subtitles(srt_file):
        """读取字幕文件并提取每条字幕的时间范围"""
        with open(srt_file, 'r', encoding='utf-8') as file:
            content = file.read()

        subtitle_pattern = r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})"
        times = re.findall(subtitle_pattern, content)

        # 返回每一条字幕的开始和结束时间
        return [(start, end) for start, end in times]

    @staticmethod
    def extract_keyframes_from_subtitle_ranges(video_path, subtitle_times, frame_redundancy):
        """
        从字幕时间范围内提取视频关键帧

        参数:
            video_path: 视频文件路径
            subtitle_times: 字幕时间列表，格式为 [(start_time, end_time), ...]
            frame_redundancy: 字幕时间前后需要额外检查的帧数

        返回:
            keyframes: 关键帧号的有序列表
        """
        keyframes = set()
        container = av.open(video_path)

        try:
            stream = container.streams.video[0]
            fps = int(stream.average_rate)
            total_frames = stream.frames

            frame_ranges = set()
            for start_time, end_time in subtitle_times:
                start_frame = FaceCaptureUtils.convert_time_to_frames(time_str=start_time, fps=fps)
                end_frame = FaceCaptureUtils.convert_time_to_frames(time_str=end_time, fps=fps)

                # 添加冗余帧范围
                for frame_num in range(max(0, start_frame - frame_redundancy),
                                       min(total_frames - 1, end_frame + frame_redundancy) + 1):
                    frame_ranges.add(frame_num)

            # 遍历视频帧，只保留在指定范围内的关键帧
            frame_index = 0
            for frame in container.decode(video=0):
                if frame_index in frame_ranges and frame.key_frame:
                    keyframes.add(frame_index)
                frame_index += 1

        except Exception as e:
            hlog.error('处理视频时出错: %s' % str(e))
        finally:
            container.close()

        result = sorted(list(keyframes))
        hlog.info('需要处理的关键帧位置-> %s' % result)
        hlog.info('获取关键帧完成')

        return result

    @staticmethod
    def is_frontal_face(region, eye_diff_threshold):
        # 正脸中眼睛的横坐标差异(threshold)通常大于 70-80 像素，小于 50 就不是正脸
        try:
            left_eye = region.get('left_eye')
            right_eye = region.get('right_eye')

            if not (left_eye and right_eye):
                hlog.error('左右眼数据缺失: left_eye=%s, right_eye=%s' % (left_eye, right_eye))
                return False

            if not (isinstance(left_eye, (tuple, list)) and isinstance(right_eye, (tuple, list))):
                hlog.error('左右眼坐标格式错误: left_eye=%s, right_eye=%s' % (left_eye, right_eye))
                return False

            if len(left_eye) != 2 or len(right_eye) != 2:
                hlog.error('左右眼坐标维度错误: left_eye=%s, right_eye=%s' % (left_eye, right_eye))
                return False

            # 计算眼睛的横坐标差异
            eye_x_diff = abs(left_eye[0] - right_eye[0])

            hlog.info('眼睛横坐标差异: %s' % eye_x_diff)

            # 如果横坐标差异大于阈值，认为是正脸
            return eye_x_diff > eye_diff_threshold  # 如果横坐标差异大于阈值，返回 True

        except Exception as e:
            hlog.error('计算面部特征时出错: %s' % str(e))
            return False

    @staticmethod
    def capture_avatar_from_video(video_path, subtitle_times, avatar_output_path, frame_redundancy, target_size,
                                  eye_diff_threshold):
        FaceCaptureUtils.ensure_directory_exists(avatar_output_path)
        # 提取视频字幕对应的帧
        video_frames = FaceCaptureUtils.extract_keyframes_from_subtitle_ranges(video_path=video_path,
                                                                               subtitle_times=subtitle_times,
                                                                               frame_redundancy=frame_redundancy)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception('无法打开视频: %s' % video_path)

        detected_faces = []

        try:
            for frame_count in video_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
                ret, frame = cap.read()
                if not ret:
                    hlog.error('无法读取第 %s 帧' % frame_count)
                    continue

                try:
                    results = DeepFace.analyze(
                        frame,
                        actions=['age', 'gender', 'race', 'emotion'],
                        detector_backend='retinaface',
                        enforce_detection=False
                    )

                    # results = FaceCaptureUtils.deepface_load_model(frame=frame)

                    if not isinstance(results, list):
                        results = [results]

                    if not results:
                        hlog.info('第 %s 帧中没有检测到人脸' % frame_count)
                        continue

                    for i, result in enumerate(results):
                        if 'face_confidence' not in result or result['face_confidence'] < 0.95:
                            hlog.warning('第 %s 帧中的人脸 %s 置信度过低，跳过\n' % (frame_count, i + 1))
                            continue

                        # 增加正脸判断
                        if 'region' in result:
                            if not FaceCaptureUtils.is_frontal_face(region=result['region'],
                                                                    eye_diff_threshold=eye_diff_threshold):
                                hlog.warning('第 %s 帧中的人脸 %s 不是正脸，跳过\n' % (frame_count, i + 1))
                                continue

                        gender_confidence = FaceCaptureUtils.get_max_prediction(predictions=result['gender'])
                        race_confidence = FaceCaptureUtils.get_max_prediction(predictions=result['race'])
                        emotion_confidence = FaceCaptureUtils.get_max_prediction(predictions=result['emotion'])

                        age = result['age']
                        gender = FaceCaptureUtils.get_enum_by_value(enum_class=GenderType,
                                                                    value=gender_confidence[0]).chinese_name
                        race = FaceCaptureUtils.get_enum_by_value(enum_class=RaceType,
                                                                  value=race_confidence[0]).chinese_name
                        emotion = FaceCaptureUtils.get_enum_by_value(enum_class=EmotionType,
                                                                     value=emotion_confidence[0]).chinese_name

                        hlog.debug('第 %s 帧中的人脸 %s ,置信度 %s, 分析结果:' % (frame_count,
                                                                                  i + 1,
                                                                                  result['face_confidence']))
                        hlog.debug('年龄: %s，' % age)
                        hlog.debug('性别: %s (置信度: %.2f%%)' % (gender, gender_confidence[1]))
                        hlog.debug('种族: %s (置信度: %.2f%%)' % (race, race_confidence[1]))
                        hlog.debug('情绪: %s (置信度: %.2f%%)' % (emotion, emotion_confidence[1]))

                        # 裁剪并调整人脸大小
                        if 'region' in result:
                            region = result['region']
                            x, y, w, h = region['x'], region['y'], region['w'], region['h']

                            if w > 0 and h > 0:
                                # 扩大裁剪区域以包含更多面部特征
                                center_x = x + w // 2
                                center_y = y + h // 2
                                size = max(w, h)
                                padding = int(size * 0.3)  # 增加30%的边距
                                new_size = size + 2 * padding

                                # 计算新的裁剪区域
                                x1 = max(0, center_x - new_size // 2)
                                y1 = max(0, center_y - new_size // 2)
                                x2 = min(frame.shape[1], x1 + new_size)
                                y2 = min(frame.shape[0], y1 + new_size)

                                # 裁剪人脸
                                cropped_face = frame[int(y1):int(y2), int(x1):int(x2)]

                                # 调整到统一大小
                                if cropped_face.size > 0:  # 确保裁剪区域有效
                                    cropped_face = cv2.resize(cropped_face, target_size,
                                                              interpolation=cv2.INTER_LANCZOS4)

                                    avatar_file = 'frame_%s_face_%s.jpg' % (frame_count, i)
                                    face_img_path = str(avatar_output_path / avatar_file)

                                    cv2.imwrite(face_img_path, cropped_face)
                                    hlog.info('人脸图片已保存到: %s\n' % face_img_path)

                                    detected_faces.append((face_img_path, age, gender, race, emotion))
                                else:
                                    hlog.error('第 %s 帧中的人脸 %s 裁剪失败' % (frame_count, i + 1))
                            else:
                                hlog.warning('第 %s 帧中的人脸 %s 位置无效，跳过' % (frame_count, i + 1))

                except Exception as e:
                    hlog.error('处理第 %s 帧时出现错误: %s' % (frame_count, e))
        finally:
            cap.release()

        return detected_faces
