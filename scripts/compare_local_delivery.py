#!/usr/bin/env python3
"""Same-line controlled Chinese delivery trials using the production policy."""
import argparse
import compare_cosyvoice3 as trial
from cosyvoice_speech import instruction

trial.OUT = trial.ROOT / 'output/local-delivery-trial'
TEXT = '明天一起去山里采药吧！回来以后，我们再一起做新的炼金道具，好不好？'
trial.SAMPLES = [(label, 'Chinese', TEXT, False) for label in ['gentle', 'standard', 'expressive', 'asmr']]
trial.INSTRUCTIONS = {label: instruction('happy', 'asmr' if label == 'asmr' else 'chat',
                                        'standard' if label == 'asmr' else label)
                      for label, *_ in trial.SAMPLES}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyze', action='store_true')
    args = parser.parse_args()
    trial.analyze() if args.analyze else trial.generate()
