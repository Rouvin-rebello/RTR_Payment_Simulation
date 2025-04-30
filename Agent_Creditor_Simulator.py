import xml.etree.ElementTree as ET
import logging
import os
from datetime import datetime
from xml.dom import minidom
from ISO20022_Pacs002_Generator import generate_pacs002_message
from ISO20022_Camt054_Generator import generate_camt054_message

class ReceiverBankSimulator:
    def save_receiver_pacs002(self, tree, debtor_bic):
        if not os.path.exists("messages/pacs002/receiver_response"):
            os.makedirs("messages/pacs002/receiver_response")
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"messages/pacs002/receiver_response/response_to_{debtor_bic}_{timestamp}.xml"
        
        # Save with pretty printing
        rough_string = ET.tostring(tree.getroot(), 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
            
        logging.info(f"Receiver PACS.002 response saved to {filename}")
        return filename

    def process_incoming_pacs008(self, pacs008_filename):
        logging.info(f"Receiver Bank processing incoming PACS.008: {pacs008_filename}")
        try:
            tree = ET.parse(pacs008_filename)
            root = tree.getroot()
            
            msg_id = root.find(".//MsgId").text
            debtor = root.find(".//Debtor").text
            
            # Generate acceptance PACS.002
            pacs002_tree = generate_pacs002_message(msg_id, "ACCP", "Payment accepted by receiver")
            pacs002_filename = self.save_receiver_pacs002(pacs002_tree, debtor)
            
            logging.info(f"Receiver Bank sent PACS.002 acceptance for message {msg_id}")
            return True, pacs002_filename
            
        except Exception as e:
            logging.error(f"Receiver Bank processing error: {str(e)}")
            return False, str(e)

    def handle_settlement_completion(self, msg_id, creditor, amount):
        """Handle settlement completion and generate CAMT.054"""
        logging.info(f"Receiver Bank handling settlement completion for {creditor}")
        try:
            # Generate and send CAMT.054 credit notification
            camt054_tree = generate_camt054_message(creditor, amount, msg_id)
            camt054_filename = self.save_camt054(camt054_tree, creditor)
            logging.info(f"Generated and sent CAMT.054 to {creditor}")
            return True, camt054_filename
        except Exception as e:
            logging.error(f"Error generating CAMT.054: {str(e)}")
            return False, str(e)

    def save_camt054(self, tree, creditor_bic):
        """Save CAMT.054 message to file"""
        if not os.path.exists("messages/camt054"):
            os.makedirs("messages/camt054")
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"messages/camt054/camt054_{creditor_bic}_{timestamp}.xml"
        
        rough_string = ET.tostring(tree.getroot(), 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
            
        logging.info(f"CAMT.054 saved to {filename}")
        return filename
