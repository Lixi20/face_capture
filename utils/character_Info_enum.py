from enum import Enum


class RaceType(Enum):
    ASIAN = 'asian'
    INDIAN = 'indian'
    BLACK = 'black'
    WHITE = 'white'
    MIDDLE_EASTERN = 'middle eastern'
    LATINO_HISPANIC = 'latino hispanic'

    @property
    def chinese_name(self):
        race_mapping = {
            RaceType.ASIAN: '亚洲人',
            RaceType.INDIAN: '印度人',
            RaceType.BLACK: '黑人',
            RaceType.WHITE: '白人',
            RaceType.MIDDLE_EASTERN: '中东人',
            RaceType.LATINO_HISPANIC: '拉丁裔'
        }
        return race_mapping[self]


class EmotionType(Enum):
    ANGRY = 'angry'
    DISGUST = 'disgust'
    FEAR = 'fear'
    HAPPY = 'happy'
    SAD = 'sad'
    SURPRISE = 'surprise'
    NEUTRAL = 'neutral'

    @property
    def chinese_name(self):
        emotion_mapping = {
            EmotionType.ANGRY: '愤怒',
            EmotionType.DISGUST: '厌恶',
            EmotionType.FEAR: '恐惧',
            EmotionType.HAPPY: '开心',
            EmotionType.SAD: '悲伤',
            EmotionType.SURPRISE: '惊讶',
            EmotionType.NEUTRAL: '平静'
        }
        return emotion_mapping[self]


class GenderType(Enum):
    MAN = 'Man'
    WOMAN = 'Woman'

    @property
    def chinese_name(self):
        gender_mapping = {
            GenderType.MAN: '男',
            GenderType.WOMAN: '女'
        }
        return gender_mapping[self]
