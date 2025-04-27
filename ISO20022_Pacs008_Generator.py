import tkinter.messagebox as messagebox
import customtkinter as ctk
import uuid
import os
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

# === Setup customtkinter ===
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")  

# === Basic Persona Data ===
users = [
    {"name": "Alice Robertson", "fi_code": "001", "account": "100123456789"},
    {"name": "Michael Chen", "fi_code": "002", "account": "200987654321"},
    {"name": "Sophia Khan", "fi_code": "003", "account": "300555777111"},
    {"name": "Ethan McLeod", "fi_code": "004", "account": "400333999888"}
]

bic_codes = {
    "001": "RBIACATTXXX",
    "002": "NPCUCATTXXX",
    "003": "MPLLCATTXXX",
    "004": "NTBKCATTXXX"
}

# === ISO 20022 Message Generator ===
def generate_iso20022_message(payer, payee, amount):
    now = datetime.now(timezone.utc) 
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") 
    msg_id = str(uuid.uuid4())
    instr_id = str(uuid.uuid4())
    e2e_id = str(uuid.uuid4())

    ns = {"": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"}
    ET.register_namespace('', ns[""])

    document = ET.Element("Document")
    fct = ET.SubElement(document, "FIToFICstmrCdtTrf")

    grp_hdr = ET.SubElement(fct, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = msg_id
    ET.SubElement(grp_hdr, "CreDtTm").text = now.isoformat() + "Z"
    ET.SubElement(grp_hdr, "NbOfTxs").text = "1"

    sttlm_inf = ET.SubElement(grp_hdr, "SttlmInf")
    ET.SubElement(sttlm_inf, "SttlmMtd").text = "CLRG"

    cdt_trf_tx_inf = ET.SubElement(fct, "CdtTrfTxInf")

    pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
    ET.SubElement(pmt_id, "InstrId").text = instr_id
    ET.SubElement(pmt_id, "EndToEndId").text = e2e_id
    ET.SubElement(pmt_id, "TxId").text = msg_id

    pmt_tp_inf = ET.SubElement(cdt_trf_tx_inf, "PmtTpInf")
    svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
    ET.SubElement(svc_lvl, "Cd").text = "URGP"
    lcl_instrm = ET.SubElement(pmt_tp_inf, "LclInstrm")
    ET.SubElement(lcl_instrm, "Cd").text = "RTR"

    ET.SubElement(cdt_trf_tx_inf, "IntrBkSttlmAmt", Ccy="CAD").text = f"{amount:.2f}"
    ET.SubElement(cdt_trf_tx_inf, "IntrBkSttlmDt").text = now.strftime("%Y-%m-%d")

    dbtr = ET.SubElement(cdt_trf_tx_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = payer["name"]

    dbtr_acct = ET.SubElement(cdt_trf_tx_inf, "DbtrAcct")
    id_tag = ET.SubElement(dbtr_acct, "Id")
    othr = ET.SubElement(id_tag, "Othr")
    ET.SubElement(othr, "Id").text = payer["account"]

    dbtr_agt = ET.SubElement(cdt_trf_tx_inf, "DbtrAgt")
    fin_instn_id = ET.SubElement(dbtr_agt, "FinInstnId")
    ET.SubElement(fin_instn_id, "BICFI").text = bic_codes[payer["fi_code"]]

    cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
    fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
    ET.SubElement(fin_instn_id, "BICFI").text = bic_codes[payee["fi_code"]]

    cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
    ET.SubElement(cdtr, "Nm").text = payee["name"]

    cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
    id_tag = ET.SubElement(cdtr_acct, "Id")
    othr = ET.SubElement(id_tag, "Othr")
    ET.SubElement(othr, "Id").text = payee["account"]

    rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
    ET.SubElement(rmt_inf, "Ustrd").text = f"Payment from {payer['name']} to {payee['name']}"

    return ET.ElementTree(document)

def save_message(tree, payer_name, payee_name):
    if not os.path.exists("messages"):
        os.makedirs("messages")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"messages/{payer_name.replace(' ', '_')}_to_{payee_name.replace(' ', '_')}_{timestamp}.xml"
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    return filename

# === GUI App ===
class PaymentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RTR Payment Simulation")
        self.geometry("500x400")
        self.resizable(False, False)

        self.logged_in_user = ctk.StringVar()
        self.recipient = ctk.StringVar()
        self.amount = ctk.StringVar()

        self.create_login_screen()

    def create_login_screen(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(expand=True, fill="both", pady=20, padx=20)

        title = ctk.CTkLabel(self.login_frame, text="Login", font=("Arial", 24))
        title.pack(pady=20)

        self.user_combo = ctk.CTkOptionMenu(self.login_frame, variable=self.logged_in_user, values=[u["name"] for u in users])
        self.user_combo.pack(pady=10)

        login_button = ctk.CTkButton(self.login_frame, text="Login", command=self.login)
        login_button.pack(pady=10)

    def login(self):
        if self.logged_in_user.get():
            self.login_frame.destroy()
            self.create_payment_screen()
        else:
            messagebox.showerror("Error", "Please select a user to log in.")

    def create_payment_screen(self):
        self.payment_frame = ctk.CTkFrame(self)
        self.payment_frame.pack(expand=True, fill="both", pady=20, padx=20)

        title = ctk.CTkLabel(self.payment_frame, text="Send Payment", font=("Arial", 24))
        title.pack(pady=20)

        self.recipient_combo = ctk.CTkOptionMenu(
            self.payment_frame, 
            variable=self.recipient, 
            values=[u["name"] for u in users if u["name"] != self.logged_in_user.get()]
        )
        self.recipient_combo.pack(pady=10)

        self.amount_entry = ctk.CTkEntry(self.payment_frame, placeholder_text="Amount (CAD)", textvariable=self.amount)
        self.amount_entry.pack(pady=10)

        send_button = ctk.CTkButton(self.payment_frame, text="Send Payment", command=self.send_payment)
        send_button.pack(pady=20)

    def send_payment(self):
        payer_name = self.logged_in_user.get()
        payee_name = self.recipient.get()
        amount_str = self.amount.get()

        if not (payer_name and payee_name and amount_str):
            messagebox.showerror("Error", "Please complete all fields.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid amount greater than 0.")
            return

        payer = next(u for u in users if u["name"] == payer_name)
        payee = next(u for u in users if u["name"] == payee_name)

        tree = generate_iso20022_message(payer, payee, amount)
        filename = save_message(tree, payer_name, payee_name)

        messagebox.showinfo("Success", f"Payment message created:\n{filename}")

if __name__ == "__main__":
    app = PaymentApp()
    app.mainloop()
