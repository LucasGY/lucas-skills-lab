#!/usr/bin/env python3
import json
from fetch_cnn_fng import fetch_payload


def main():
    payload = fetch_payload()
    current = payload['fear_and_greed']
    result = {
        'score': round(current['score'], 1),
        'rating': current['rating'],
        'timestamp': current['timestamp'],
        'previous_close': current['previous_close'],
        'previous_1_week': current['previous_1_week'],
        'previous_1_month': current['previous_1_month'],
        'previous_1_year': current['previous_1_year'],
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
