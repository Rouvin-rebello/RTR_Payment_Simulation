import os
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
from RTR_Settlement_Processor import RTRSettlementProcessor
from ISO20022_Pacs002_Generator import generate_pacs002_message, save_pacs002_message
from Agent_Creditor_Simulator import ReceiverBankSimulator

# Setup logging for settlement simulation
logging.basicConfig(filename='settlement_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Update FIs list to use correct BIC codes
FIs = ["BOFCUS3NXXX", "CHASUS33XXX", "CITIUS33XXX"]

# Simulated Processor to Accept, Validate, Route, and Settle Payments
class RTRExchangeProcessor:
    def __init__(self):
        self.settlement_processor = RTRSettlementProcessor()
        self.receiver_bank = ReceiverBankSimulator()

    def forward_to_receiver(self, original_tree, creditor_bic):
        logging.info(f"Forwarding PACS.008 message to receiving bank: {creditor_bic}")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create a copy of the original message
        forward_tree = ET.ElementTree(ET.fromstring(ET.tostring(original_tree.getroot())))
        
        # Update the message ID for forwarding
        msg_id = forward_tree.find(".//MsgId")
        msg_id.text = f"FWD-{timestamp}"
        
        # Save forwarded message
        if not os.path.exists("messages/pacs008/forwarded"):
            os.makedirs("messages/pacs008/forwarded")
            
        filename = f"messages/pacs008/forwarded/to_{creditor_bic}_{timestamp}.xml"
        forward_tree.write(filename, encoding='utf-8', xml_declaration=True)
        logging.info(f"Forwarded PACS.008 saved to {filename}")
        return filename

    def send_settlement_notifications(self, msg_id_value, debtor_value, creditor_value):
        logging.info(f"Sending settlement completion notifications to {debtor_value} and {creditor_value}")
        
        # Generate and save PACS.002 for debtor
        debtor_pacs002 = generate_pacs002_message(msg_id_value, "ACSC", "Settlement completed successfully")
        debtor_notification = save_pacs002_message(debtor_pacs002, debtor_value, "settlement_complete")
        
        # Generate and save PACS.002 for creditor
        creditor_pacs002 = generate_pacs002_message(msg_id_value, "ACSC", "Settlement completed successfully")
        creditor_notification = save_pacs002_message(creditor_pacs002, creditor_value, "settlement_complete")
        
        logging.info("Settlement notifications sent to both parties")
        return debtor_notification, creditor_notification

    def process_message(self, xml_file_path):
        logging.info(f"Processing payment message from file: {xml_file_path}")
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
            msg_id = root.find(".//MsgId")

            # Step 3: Validate mandatory fields
            if debtor is None or creditor is None or amount is None or msg_id is None or not debtor.text.strip() or not creditor.text.strip() or not amount.text.strip() or not msg_id.text.strip():
                logging.error(f"Validation Failed: Missing mandatory fields in {xml_file_path}")
                return "Settlement Failed: Missing mandatory fields."

            debtor_value = debtor.text.strip()
            creditor_value = creditor.text.strip()
            amount_value = amount.text.strip()
            msg_id_value = msg_id.text.strip()

            # Ensure Amount is a valid number
            try:
                amount_value = float(amount_value)
            except ValueError:
                logging.error(f"Settlement Failed: Invalid amount in {xml_file_path}.")
                return "Settlement Failed: Invalid amount format."

            logging.info(f"Message validation successful for payment of {amount_value} from {debtor_value} to {creditor_value}")

            # After successful validation, send acknowledgment
            pacs002_tree = generate_pacs002_message(msg_id_value, "ACCP")
            pacs002_filename = save_pacs002_message(pacs002_tree, debtor_value)
            logging.info(f"Generated PACS.002 acknowledgment for {debtor_value}")

            # Forward PACS.008 to receiving bank
            forwarded_filename = self.forward_to_receiver(tree, creditor_value)
            logging.info(f"PACS.008 message forwarded to receiving bank {creditor_value}")

            # Wait for receiver's PACS.002
            success, receiver_response = self.receiver_bank.process_incoming_pacs008(forwarded_filename)
            if not success:
                logging.error(f"Receiver bank rejected payment: {receiver_response}")
                return "Settlement Failed: Receiver bank rejected payment"
            
            logging.info("Received acceptance PACS.002 from receiver bank")

            # Continue with routing and settlement only after receiver acceptance
            routing_status = self.route_payment(debtor_value, creditor_value, amount_value)

            # Step 5: Settle the payment and log the outcome
            if routing_status == "Success":
                settlement_status = self.settle_payment(debtor_value, creditor_value, amount_value)
                if "Success" in settlement_status:
                    # Send settlement completion notifications
                    self.send_settlement_notifications(msg_id_value, debtor_value, creditor_value)
                    
                    # Notify receiver bank of settlement completion
                    self.receiver_bank.handle_settlement_completion(msg_id_value, creditor_value, amount_value)
                    
                return settlement_status
            else:
                logging.error(f"Settlement Failed: Routing issue with {debtor_value} and {creditor_value}.")
                return "Settlement Failed: Routing issue."
        
        except ET.ParseError:
            logging.error(f"Settlement Failed: XML parsing error in {xml_file_path}.")
            if 'msg_id_value' in locals():
                # Send negative acknowledgment
                pacs002_tree = generate_pacs002_message(msg_id_value, "RJCT", "Invalid message format")
                save_pacs002_message(pacs002_tree, debtor_value)
            return "Settlement Failed: XML parsing error."

    def route_payment(self, debtor, creditor, amount):
        logging.info(f"Validating routing for payment of {amount} from {debtor} to {creditor}")
        # Route using BIC codes
        logging.info(f"Attempting to route payment to {creditor}")
        if creditor in FIs and debtor in FIs:
            logging.info(f"Routing payment to {creditor} for {amount}")
            return "Success"
        else:
            logging.error(f"Routing error: Invalid BIC codes - Debtor: {debtor}, Creditor: {creditor}")
            return "Failure"

    def settle_payment(self, debtor, creditor, amount):
        logging.info(f"Initiating settlement for payment of {amount} from {debtor} to {creditor}")
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
