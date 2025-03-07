from happy_python.happy_config import HappyConfigBase

class PublicConfig(HappyConfigBase):
    def __init__(self):
        super().__init__()

        self.section = 'main'
        self.mod_name = ''
        self.active = True
        self.debug = 3
        self.dry_run = False
        self.frame_redundancy = 50
        self.image_width = 300
        self.image_height = 300
        self.eye_diff_threshold = 50


class PrivateConfig(HappyConfigBase):
    def __init__(self):
        super().__init__()

        self.section = 'face_conf.custom'
        self.video_path = ''
        self.sub_path = ''
        self.avatar_output_path = ''