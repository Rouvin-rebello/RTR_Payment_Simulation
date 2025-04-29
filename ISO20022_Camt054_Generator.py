import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import logging
from xml.dom import minidom

def generate_camt054_message(creditor_bic, amount, msg_id):
    logging.info(f"Generating CAMT.054 credit notification for {creditor_bic}")
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d-%H%M%S")
    
    document = ET.Element("Document")
    bank_to_cust_debt_credit_notif = ET.SubElement(document, "BkToCstmrDbtCdtNtfctn")
    
    # Group Header
    grp_hdr = ET.SubElement(bank_to_cust_debt_credit_notif, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = f"CAMT054-{timestamp}"
    ET.SubElement(grp_hdr, "CreDtTm").text = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Notification
    ntfctn = ET.SubElement(bank_to_cust_debt_credit_notif, "Ntfctn")
    ET.SubElement(ntfctn, "Id").text = f"CRED-{timestamp}"
    ET.SubElement(ntfctn, "CreDtTm").text = now.strftime("%Y-%m-%dT%H:%M:%S")
    ET.SubElement(ntfctn, "Acct").text = creditor_bic
    ET.SubElement(ntfctn, "TxsSummry").text = f"Credit: {amount:.2f}"
    ET.SubElement(ntfctn, "RltdRef").text = msg_id
    
    return ET.ElementTree(document)

def save_camt054_message(tree, creditor_bic):
    if not os.path.exists("messages/camt054"):
        os.makedirs("messages/camt054")
        
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"messages/camt054/camt054_{creditor_bic}_{timestamp}.xml"
    
    rough_string = ET.tostring(tree.getroot(), 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    logging.info(f"CAMT.054 notification saved to {filename}")
    return filename
