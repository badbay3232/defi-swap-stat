"""
Token Velocity Tracker — утилита для анализа "скорости" движения токенов:
насколько часто и быстро они переходят из рук в руки за последние N дней.
"""

import requests
import argparse
import time
from collections import defaultdict
from datetime import datetime, timedelta


ETHERSCAN_API = "https://api.etherscan.io/api"


def fetch_token_transfers(contract_address, api_key, days=7):
    end_time = int(time.time())
    start_time = end_time - days * 86400

    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": api_key
    }

    response = requests.get(ETHERSCAN_API, params=params)
    if response.status_code != 200:
        print("Ошибка запроса к Etherscan.")
        return []

    txs = response.json().get("result", [])
    filtered = [
        tx for tx in txs
        if int(tx["timeStamp"]) >= start_time
    ]
    return filtered


def calculate_velocity(transfers):
    holders = defaultdict(set)
    timestamps = []

    for tx in transfers:
        from_addr = tx["from"]
        to_addr = tx["to"]
        ts = int(tx["timeStamp"])
        timestamps.append(ts)
        holders[to_addr].add(ts)

    num_holders = len(holders)
    tx_count = len(transfers)

    if not timestamps:
        return {"velocity": 0, "tx_count": 0, "holders": 0}

    time_span_days = (max(timestamps) - min(timestamps)) / 86400 or 1
    velocity = tx_count / time_span_days

    return {
        "velocity": round(velocity, 2),
        "tx_count": tx_count,
        "holders": num_holders,
        "days": round(time_span_days, 1)
    }


def main():
    parser = argparse.ArgumentParser(description="Анализ скорости обращения токенов.")
    parser.add_argument("contract", help="Контрактный адрес токена (ERC-20)")
    parser.add_argument("api_key", help="Etherscan API Key")
    parser.add_argument("--days", type=int, default=7, help="Период анализа в днях (по умолчанию 7)")
    args = parser.parse_args()

    print(f"[•] Получаем данные за {args.days} дней...")
    transfers = fetch_token_transfers(args.contract, args.api_key, args.days)

    print(f"[✓] Найдено {len(transfers)} трансферов. Расчёт velocity...")
    stats = calculate_velocity(transfers)

    print("\n📊 Velocity статистика:")
    print(f"- Период анализа: {stats['days']} дн.")
    print(f"- Кол-во уникальных держателей: {stats['holders']}")
    print(f"- Всего трансферов: {stats['tx_count']}")
    print(f"- Скорость (tx/день): {stats['velocity']}")


if __name__ == "__main__":
    main()
