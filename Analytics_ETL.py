import re
import json
from datetime import datetime
import os
import pandas as pd
import logging

# File paths
INPUT_FILE = 'output/parsed_transactions.json'
OUTPUT_FILE = 'output/transaction data.csv'

FAKE_BIC_MAP = {
    'ABC Corporation': 'BOFCUS3NXXX',
    'Potato Inc.': 'CHASUS33XXX',
    'Wallet LLC': 'TDOMCATTTOR'
}

def parse_log_file(log_file_path):
    parsed_data = []
    transaction_id = None
    sender = receiver = amount = status = None

    with open(log_file_path, 'r') as file:
        for line in file:
            match = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.+)$", line)
            if match:
                timestamp_str, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")

                if "Initiating payment from" in message:
                    parts = re.findall(r"from (.+?) to (.+?) for amount (\d+\.\d+)", message)
                    if parts:
                        sender, receiver, amount = parts[0]

                elif "Generating PACS.002 acknowledgment for message" in message:
                    tx_id_match = re.search(r"message (\S+)", message)
                    if tx_id_match:
                        transaction_id = tx_id_match.group(1)

                elif "Settlement status:" in message:
                    status_match = re.search(r"Settlement status: (.+)$", message)
                    if status_match:
                        status = status_match.group(1)

                        # Save the complete transaction
                        parsed_data.append({
                            "timestamp": timestamp,
                            "transaction_id": transaction_id,
                            "sender": sender,
                            "receiver": receiver,
                            "amount": float(amount),
                            "status": status
                        })

                        # Reset for next transaction
                        transaction_id = sender = receiver = amount = status = None

    return parsed_data


def enrich_transaction(tx):
    tx['sender_bic'] = FAKE_BIC_MAP.get(tx['sender'], 'UNKNOWN')
    tx['receiver_bic'] = FAKE_BIC_MAP.get(tx['receiver'], 'UNKNOWN')
    try:
        tx['timestamp'] = pd.to_datetime(tx['timestamp'])
    except Exception as e:
        tx['timestamp'] = pd.NaT
    tx['status_clean'] = 'Success' if 'Success' in tx['status'] else 'Failure'
    return tx

def etl_pipeline():
    # Extract
    with open(INPUT_FILE, 'r') as f:
        transactions = json.load(f)

    # Transform
    enriched_transactions = [enrich_transaction(tx) for tx in transactions]
    df = pd.DataFrame(enriched_transactions)

    # Optional: sort by time
    df = df.sort_values(by='timestamp')

    # Load
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"ETL complete. CSV written to: {OUTPUT_FILE}")

def run_etl():
    os.makedirs("output", exist_ok=True)
    logs_path = "settlement_log.txt"
    parsed_output = parse_log_file(logs_path)

    with open("output/parsed_transactions.json", "w") as out_file:
        json.dump(parsed_output, out_file, indent=4, default=str)

    print(f"Parsed {len(parsed_output)} transactions.")

    etl_pipeline()
    print("ETL pipeline executed successfully.")
    
    if run_etl():
        print("Analytics ETL process executed successfully.")
    else:
        print("Analytics ETL process failed.")

def run_etl():
    os.makedirs("output", exist_ok=True)
    logs_path = "settlement_log.txt"
    parsed_output = parse_log_file(logs_path)

    with open("output/parsed_transactions.json", "w") as out_file:
        json.dump(parsed_output, out_file, indent=4, default=str)

    print(f"Parsed {len(parsed_output)} transactions.")

    etl_pipeline()
    print("ETL pipeline executed successfully.")


if __name__ == "__main__":
    run_etl()
