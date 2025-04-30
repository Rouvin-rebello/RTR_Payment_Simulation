import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
from xml.dom import minidom
import logging


logging.basicConfig(level=logging.INFO)

def generate_pain001_message(payer, payee, amount):
    logging.info(f"Creating PAIN.001 message structure for {payer['name']} to {payee['name']}")
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d-%H%M%S")
    document = ET.Element("Document")
    cstmr_cdt_trf_initn = ET.SubElement(document, "CstmrCdtTrfInitn")
    
    # Group Header
    grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = f"PAIN001-{timestamp}"
    ET.SubElement(grp_hdr, "CreDtTm").text = now.strftime("%Y-%m-%dT%H:%M:%S")
    ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
    
    # Payment Information
    pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
    ET.SubElement(pmt_inf, "PmtInfId").text = f"PMT-{timestamp}"
    ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
    
    # Debtor Information
    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = payer["name"]
    dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
    ET.SubElement(dbtr_acct, "Id").text = str(payer["id"])
    dbtr_agt = ET.SubElement(pmt_inf, "DbtrAgt")
    ET.SubElement(dbtr_agt, "FinInstnId").text = payer["bic_code"]
    
    # Credit Transfer Details
    cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
    ET.SubElement(cdt_trf_tx_inf, "Amt").text = f"{amount:.2f}"
    
    # Creditor Information
    cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
    ET.SubElement(cdtr, "Nm").text = payee["name"]
    cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
    ET.SubElement(cdtr_acct, "Id").text = str(payee["id"])
    cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
    ET.SubElement(cdtr_agt, "FinInstnId").text = payee["bic_code"]
    
    logging.info(f"PAIN.001 message structure created with ID: PAIN001-{timestamp}")
    return ET.ElementTree(document)

def save_pain001_message(tree, payer_name):
    logging.info(f"Saving PAIN.001 message for {payer_name}")
    if not os.path.exists("messages/pain001"):
        os.makedirs("messages/pain001")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"messages/pain001/pain001_{payer_name.replace(' ', '_')}_{timestamp}.xml"
    
    rough_string = ET.tostring(tree.getroot(), 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    logging.info(f"PAIN.001 message successfully saved to {filename}")
    return filename
