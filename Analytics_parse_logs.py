import re
import json
from datetime import datetime
import os


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


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    logs_path = "settlement_log.txt"
    parsed_output = parse_log_file(logs_path)

    with open("output/parsed_transactions.json", "w") as out_file:
        json.dump(parsed_output, out_file, indent=4, default=str)

    print(f"Parsed {len(parsed_output)} transactions.")
