import os
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
from RTR_Settlement_Processor import RTRSettlementProcessor

# Setup logging for settlement simulation
logging.basicConfig(filename='settlement_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Update FIs list to use correct BIC codes
FIs = ["BOFCUS3NXXX", "CHASUS33XXX", "CITIUS33XXX"]

# Simulated Processor to Accept, Validate, Route, and Settle Payments
class RTRExchangeProcessor:
    def __init__(self):
        self.settlement_processor = RTRSettlementProcessor()

    def process_message(self, xml_file_path):
        # Step 1: Read the incoming XML file
        if not os.path.exists(xml_file_path):
            logging.error(f"Error: XML file not found at {xml_file_path}")
            return "Settlement Failed: File not found."

        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Step 2: Extract necessary fields (Debtor, Creditor, Amount)
            debtor = root.find(".//Debtor")
            creditor = root.find(".//Creditor")
            amount = root.find(".//Amt")

            # Step 3: Validate mandatory fields
            if debtor is None or creditor is None or amount is None or not debtor.text.strip() or not creditor.text.strip() or not amount.text.strip():
                logging.error(f"Settlement Failed: Missing mandatory fields in {xml_file_path}.")
                return "Settlement Failed: Missing mandatory fields."

            debtor_value = debtor.text.strip()
            creditor_value = creditor.text.strip()
            amount_value = amount.text.strip()

            # Ensure Amount is a valid number
            try:
                amount_value = float(amount_value)
            except ValueError:
                logging.error(f"Settlement Failed: Invalid amount in {xml_file_path}.")
                return "Settlement Failed: Invalid amount format."

            # Step 4: Routing the valid messages to the appropriate FI
            routing_status = self.route_payment(debtor_value, creditor_value, amount_value)

            # Step 5: Settle the payment and log the outcome
            if routing_status == "Success":
                settlement_status = self.settle_payment(debtor_value, creditor_value, amount_value)
                return settlement_status
            else:
                logging.error(f"Settlement Failed: Routing issue with {debtor_value} and {creditor_value}.")
                return "Settlement Failed: Routing issue."
        
        except ET.ParseError:
            logging.error(f"Settlement Failed: XML parsing error in {xml_file_path}.")
            return "Settlement Failed: XML parsing error."

    def route_payment(self, debtor, creditor, amount):
        # Route using BIC codes
        logging.info(f"Attempting to route payment to {creditor}")
        if creditor in FIs and debtor in FIs:
            logging.info(f"Routing payment to {creditor} for {amount}")
            return "Success"
        else:
            logging.error(f"Routing error: Invalid BIC codes - Debtor: {debtor}, Creditor: {creditor}")
            return "Failure"

    def settle_payment(self, debtor, creditor, amount):
        logging.info(f"Settling payment from {debtor} to {creditor} of amount {amount}")
        settlement_status = self.settlement_processor.settle_transaction(debtor, creditor, amount)
        logging.info(f"Settlement status: {settlement_status}")
        return settlement_status

# Simulated service run
if __name__ == "__main__":
    processor = RTRExchangeProcessor()

    # Test case: Simulate incoming XML file processing
    test_xml_file = "payment_request.xml"  # This should be replaced with an actual file path

    # Output the result of the processing
    result = processor.process_message(test_xml_file)
    print(result)
