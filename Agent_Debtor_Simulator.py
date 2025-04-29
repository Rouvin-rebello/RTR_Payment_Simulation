import xml.etree.ElementTree as ET
from ISO20022_Pacs008_Generator import generate_iso20022_message, save_message

class FISimulator:
    def process_pain001(self, pain001_filename):
        try:
            # Parse the PAIN.001 message
            tree = ET.parse(pain001_filename)
            root = tree.getroot()
            
            # Extract payment information
            debtor = root.find(".//Dbtr/Nm").text
            debtor_agt = root.find(".//DbtrAgt/FinInstnId").text
            creditor = root.find(".//Cdtr/Nm").text
            creditor_agt = root.find(".//CdtrAgt/FinInstnId").text
            amount = float(root.find(".//Amt").text)
            
            # Create payment info dictionary
            payer = {"name": debtor, "bic_code": debtor_agt}
            payee = {"name": creditor, "bic_code": creditor_agt}
            
            # Generate and save PACS.008 message
            pacs008_tree = generate_iso20022_message(payer, payee, amount)
            pacs008_filename = save_message(pacs008_tree, debtor, creditor)
            
            return True, pacs008_filename
            
        except Exception as e:
            return False, f"FI Processing Error: {str(e)}"
