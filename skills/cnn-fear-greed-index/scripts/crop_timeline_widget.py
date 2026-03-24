#!/usr/bin/env python3
import argparse
from pathlib import Path

from PIL import Image


PRESETS = {
    'timeline': (0, 35, 920, 455),
    'overview': (0, 35, 900, 420),
}


def main():
    parser = argparse.ArgumentParser(description='Crop CNN Fear & Greed widget screenshots and remove the right sidebar.')
    parser.add_argument('src', help='Viewport screenshot path')
    parser.add_argument('dst', help='Output crop path')
    parser.add_argument('--mode', choices=sorted(PRESETS), default='timeline')
    parser.add_argument('--left', type=int)
    parser.add_argument('--top', type=int)
    parser.add_argument('--right', type=int)
    parser.add_argument('--bottom', type=int)
    args = parser.parse_args()

    left, top, right, bottom = PRESETS[args.mode]
    if args.left is not None:
        left = args.left
    if args.top is not None:
        top = args.top
    if args.right is not None:
        right = args.right
    if args.bottom is not None:
        bottom = args.bottom

    src = Path(args.src)
    dst = Path(args.dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(src)
    img.crop((left, top, right, bottom)).save(dst)
    print(dst)


if __name__ == '__main__':
    main()
