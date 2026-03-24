#!/usr/bin/env python3
from pathlib import Path
from urllib.request import Request, urlopen
import argparse


PAGE_URL = 'https://www.cnn.com/markets/fear-and-greed'


def main():
    parser = argparse.ArgumentParser(description='Download CNN Fear & Greed page locally and inject base href.')
    parser.add_argument('out', nargs='?', default='outputs/cnn-fear-greed/cnn-fear-greed-page.html')
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    req = Request(
        PAGE_URL,
        headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
    )
    html = urlopen(req, timeout=30).read().decode('utf-8', errors='replace')
    if '<head>' in html:
        html = html.replace('<head>', '<head><base href="https://www.cnn.com/">', 1)
    out.write_text(html, encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
