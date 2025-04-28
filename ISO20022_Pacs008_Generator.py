import os
import sqlite3
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from xml.dom import minidom
from RTR_Exchange_Processor import RTRExchangeProcessor

# === Database Connection Management ===
def get_db_connection():
    conn = sqlite3.connect('payment_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT users.*, bic_codes.bic_code FROM users JOIN bic_codes ON users.fi_code = bic_codes.fi_code")
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_by_name(name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.*, bic_codes.bic_code 
        FROM users 
        JOIN bic_codes ON users.fi_code = bic_codes.fi_code 
        WHERE users.name = ?
    """, (name,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

# === ISO 20022 Message Generator ===
def generate_iso20022_message(payer, payee, amount):
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d-%H%M%S")
    
    document = ET.Element("Document")
    fct = ET.SubElement(document, "FIToFICstmrCdtTrf")
    
    # Group Header - simplified
    grp_hdr = ET.SubElement(fct, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = timestamp
    ET.SubElement(grp_hdr, "CreDtTm").text = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Credit Transfer Transaction Information - simplified
    cdt_trf_tx_inf = ET.SubElement(fct, "CdtTrfTxInf")
    
    # Payment ID
    pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
    ET.SubElement(pmt_id, "EndToEndId").text = f"{timestamp}"
    
    # Amount
    ET.SubElement(cdt_trf_tx_inf, "Amt").text = f"{amount:.2f}"
    
    # Use BIC codes for Debtor and Creditor
    ET.SubElement(cdt_trf_tx_inf, "Debtor").text = payer["bic_code"]
    ET.SubElement(cdt_trf_tx_inf, "Creditor").text = payee["bic_code"]

    return ET.ElementTree(document)

def save_message(tree, payer_name, payee_name):
    if not os.path.exists("messages"):
        os.makedirs("messages")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"messages/{payer_name.replace(' ', '_')}_to_{payee_name.replace(' ', '_')}_{timestamp}.xml"
    
    # Convert ElementTree to string
    rough_string = ET.tostring(tree.getroot(), 'utf-8')
    # Create pretty-printed XML string
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file with proper formatting
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    return filename

def process_through_rtr(filename):
    processor = RTRExchangeProcessor()
    return processor.process_message(filename)
