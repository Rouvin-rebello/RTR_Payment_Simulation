import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
from xml.dom import minidom
import logging

def generate_pacs002_message(original_message_id, status, reason=None):
    logging.info(f"Generating PACS.002 acknowledgment for message {original_message_id}")
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d-%H%M%S")
    
    document = ET.Element("Document")
    fi_to_fi_pmt_sts_rpt = ET.SubElement(document, "FIToFIPmtStsRpt")
    
    # Group Header
    grp_hdr = ET.SubElement(fi_to_fi_pmt_sts_rpt, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = f"PACS002-{timestamp}"
    ET.SubElement(grp_hdr, "CreDtTm").text = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Original Group Information
    org_grp_inf = ET.SubElement(fi_to_fi_pmt_sts_rpt, "OrgnlGrpInfAndSts")
    ET.SubElement(org_grp_inf, "OrgnlMsgId").text = original_message_id
    ET.SubElement(org_grp_inf, "OrgnlMsgNmId").text = "pacs.008.001.01"
    ET.SubElement(org_grp_inf, "GrpSts").text = status
    
    if reason:
        sts_rsn = ET.SubElement(org_grp_inf, "StsRsn")
        ET.SubElement(sts_rsn, "Rsn").text = reason
    
    return ET.ElementTree(document)

def save_pacs002_message(tree, bank_bic, message_type="response"):
    if not os.path.exists(f"messages/pacs002/{message_type}"):
        os.makedirs(f"messages/pacs002/{message_type}")
        
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"messages/pacs002/{message_type}/pacs002_{bank_bic}_{timestamp}.xml"
    
    rough_string = ET.tostring(tree.getroot(), 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    logging.info(f"PACS.002 {message_type} message saved to {filename}")
    return filename
