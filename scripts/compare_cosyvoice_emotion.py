#!/usr/bin/env python3
"""Chinese CosyVoice emotion samples; same reference/seed as the baseline trial."""
import argparse
import compare_cosyvoice3 as trial
from cosyvoice_speech import HAPPY, GENTLE

trial.OUT = trial.ROOT / 'output/cosyvoice3-emotion'
TEXT = '我是莱莎，最喜欢用炼金术制作新的道具。明天一起去山里采药吧！'
trial.SAMPLES = [
    ('zh-cross', 'Chinese', TEXT, False),
    ('zh-happy', 'Chinese', TEXT, False),
    ('zh-gentle', 'Chinese', '别担心，我会陪着你的。先休息一会儿，我们再一起想办法，好吗？', False),
]
trial.INSTRUCTIONS = {'zh-happy': HAPPY, 'zh-gentle': GENTLE}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyze', action='store_true')
    args = parser.parse_args()
    trial.analyze() if args.analyze else trial.generate()
