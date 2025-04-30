import tkinter.messagebox as messagebox
import customtkinter as ctk
import sqlite3
import logging
from ISO20022_Pacs008_Generator import (
    get_all_users,
    get_user_by_name,
    generate_iso20022_message,
    save_message,
    process_through_rtr
)
from ISO20022_Pain001_Generator import generate_pain001_message, save_pain001_message
from db_manager import reset_db
from Agent_Debtor_Simulator import FISimulator

# Configure logging
logging.basicConfig(filename='settlement_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# === Setup customtkinter ===
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")  

class PaymentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RTR Payment Simulation")
        self.geometry("800x600") 
        self.resizable(False, False)

        # Configure fonts and colors
        self.title_font = ("Helvetica", 28, "bold")
        self.heading_font = ("Helvetica", 20, "bold")
        self.label_font = ("Helvetica", 14)
        self.button_font = ("Helvetica", 14)
        
        self.logged_in_user = ctk.StringVar()
        self.recipient = ctk.StringVar()
        self.amount = ctk.StringVar()

        self.users = get_all_users()
        self.create_login_screen()

    def create_login_screen(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(expand=True, fill="both", pady=40, padx=40)

        # Main title with styling
        title = ctk.CTkLabel(
            self.login_frame, 
            text="RTR Payment System",
            font=self.title_font
        )
        title.pack(pady=(30, 40))

        # Login section with frame
        login_section = ctk.CTkFrame(self.login_frame)
        login_section.pack(fill="x", padx=100, pady=20)

        # User selection with label
        user_label = ctk.CTkLabel(
            login_section,
            text="Select Your Account",
            font=self.heading_font
        )
        user_label.pack(pady=(20, 10))

        self.user_combo = ctk.CTkOptionMenu(
            login_section,
            variable=self.logged_in_user,
            values=[u['name'] for u in self.users],
            font=self.label_font,
            width=300
        )
        self.user_combo.pack(pady=20)

        # Buttons container
        button_frame = ctk.CTkFrame(login_section)
        button_frame.pack(pady=20)

        login_button = ctk.CTkButton(
            button_frame,
            text="Login",
            command=self.login,
            font=self.button_font,
            width=200,
            height=40
        )
        login_button.pack(pady=10)

        reset_button = ctk.CTkButton(
            button_frame,
            text="Reset Database",
            command=self.reset_database,
            font=self.button_font,
            fg_color="red",
            hover_color="darkred",
            width=200,
            height=40
        )
        reset_button.pack(pady=10)

    def reset_database(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the database? This will reset all balances and transactions."):
            success, message = reset_db()
            if success:
                messagebox.showinfo("Success", message)
                # Refresh the application
                self.login_frame.destroy()
                self.users = get_all_users()
                self.create_login_screen()
            else:
                messagebox.showerror("Error", message)

    def login(self):
        if self.logged_in_user.get():
            self.login_frame.destroy()
            self.create_payment_screen()
        else:
            messagebox.showerror("Error", "Please select a user to log in.")

    def create_payment_screen(self):
        self.payment_frame = ctk.CTkFrame(self)
        self.payment_frame.pack(expand=True, fill="both", pady=40, padx=40)

        # Create scrollable main container
        main_container = ctk.CTkScrollableFrame(self.payment_frame)
        main_container.pack(expand=True, fill="both", padx=20, pady=20)

        # Header section
        header_frame = ctk.CTkFrame(main_container)
        header_frame.pack(fill="x", pady=(0, 20))

        title = ctk.CTkLabel(
            header_frame,
            text="Send Payment",
            font=self.title_font
        )
        title.pack(pady=10)

        user = get_user_by_name(self.logged_in_user.get())
        balance_label = ctk.CTkLabel(
            header_frame,
            text=f"Available Balance: ${user['balance']:.2f}",
            font=self.heading_font
        )
        balance_label.pack(pady=10)

        # Payment form section
        form_frame = ctk.CTkFrame(main_container)
        form_frame.pack(fill="x", pady=10)

        recipient_label = ctk.CTkLabel(
            form_frame,
            text="Select Recipient:",
            font=self.label_font
        )
        recipient_label.pack(pady=(20, 5))

        self.recipient_combo = ctk.CTkOptionMenu(
            form_frame,
            variable=self.recipient,
            values=[u['name'] for u in self.users if u['name'] != self.logged_in_user.get()],
            font=self.label_font,
            width=300
        )
        self.recipient_combo.pack(pady=(0, 20))

        amount_label = ctk.CTkLabel(
            form_frame,
            text="Enter Amount (CAD):",
            font=self.label_font
        )
        amount_label.pack(pady=(20, 5))

        self.amount_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="0.00",
            textvariable=self.amount,
            font=self.label_font,
            width=300
        )
        self.amount_entry.pack(pady=(0, 30))

        send_button = ctk.CTkButton(
            form_frame,
            text="Send Payment",
            command=self.send_payment,
            font=self.button_font,
            width=300,
            height=50
        )
        send_button.pack(pady=(0, 30))

        # Process Tracker Frame
        tracker_label = ctk.CTkLabel(
            main_container,
            text="Payment Process Tracker",
            font=self.heading_font
        )
        tracker_label.pack(pady=(20, 10))

        self.tracker_frame = ctk.CTkFrame(main_container)
        self.tracker_frame.pack(fill="x", pady=(0, 20))

        # Process steps and their checkboxes
        self.process_steps = [
            "Debtor Simulator Created PAIN.001 message",
            "Debtor Simulator Sent PAIN.001 to Debtor Agent",
            "Debtor Agent Created PACS.008",
            "Debtor Agent Sent PACS.008 to Exchange",
            "Exchange validated PACS.008",
            "Exchange Created PACS.002",
            "Exchange Sent PACS.002 to Debtor Agent",
            "Exchange component created PACS.008",
            "Exchange sent PACS.008 to Creditor Agent",
            "PACS.002 from Creditor Agent",
            "Creditor Agent created PACS.002",
            "Creditor Agent sent PACS.002 to Exchange",
            "Settlement in progress",
            "Exchange sent PACS.002 to Debtor/Creditor Agent",
            "Creditor Agent created CAMT.054",
            "Creditor Agent sent CAMT.054 to Creditor Simulator"
        ]
        
        self.checkboxes = []
        for step in self.process_steps:
            step_frame = ctk.CTkFrame(self.tracker_frame, fg_color="transparent")
            step_frame.pack(fill="x", pady=5)
            
            checkbox = ctk.CTkCheckBox(
                step_frame, 
                text=step,
                state="disabled",
                font=("Helvetica", 12)
            )
            checkbox.pack(side="left", padx=20)
            self.checkboxes.append(checkbox)

        # Adjust window size to accommodate all elements
        self.geometry("800x800")

    def update_process_status(self, step_index):
        self.checkboxes[step_index].select()
        self.update()

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

        payer = get_user_by_name(payer_name)
        payee = get_user_by_name(payee_name)

        # Check sufficient funds
        if payer['balance'] < amount:
            messagebox.showerror("Error", "Insufficient funds")
            return

        try:
            logging.info(f"Initiating payment from {payer_name} to {payee_name} for amount {amount}")
            conn = sqlite3.connect('payment_system.db')
            cursor = conn.cursor()

            # Reset checkboxes
            for checkbox in self.checkboxes:
                checkbox.deselect()

            # Generate PAIN.001 message
            self.update_process_status(0)  # Debtor Simulator Created PAIN.001
            pain001_tree = generate_pain001_message(payer, payee, amount)
            pain001_filename = save_pain001_message(pain001_tree, payer_name)
            self.update_process_status(1)  # Debtor Simulator Sent PAIN.001
            
            # Process through FI Simulator
            fi_simulator = FISimulator()
            success, result = fi_simulator.process_pain001(pain001_filename)
            self.update_process_status(2)  # Debtor Agent Created PACS.008
            
            if not success:
                logging.error(f"FI Processing Error: {result}")
                messagebox.showerror("FI Processing Error", result)
                return
                
            pacs008_filename = result
            self.update_process_status(3)  # Debtor Agent Sent PACS.008

            # Process through RTR Exchange
            self.update_process_status(4)  # Exchange validated PACS.008
            self.update_process_status(5)  # Exchange Created PACS.002
            self.update_process_status(6)  # Exchange Sent PACS.002 to Debtor Agent
            self.update_process_status(7)  # Exchange component created PACS.008
            self.update_process_status(8)  # Exchange sent PACS.008 to Creditor Agent
            rtr_result = process_through_rtr(pacs008_filename)
            
            if "Success" in rtr_result:
                # Simulate remaining steps
                self.update_process_status(9)   # PACS.002 from Creditor Agent
                self.update_process_status(10)  # Creditor Agent created PACS.002
                self.update_process_status(11)  # Creditor Agent sent PACS.002 to Exchange
                self.update_process_status(12)  # Settlement in progress
                self.update_process_status(13)  # Exchange sent PACS.002 to Debtor/Creditor
                self.update_process_status(14)  # Creditor Agent created CAMT.054
                self.update_process_status(15)  # Creditor Agent sent CAMT.054

                # Log the transaction
                cursor.execute("""
                    INSERT INTO transactions (sender_id, receiver_id, amount)
                    SELECT s.id, r.id, ?
                    FROM users s, users r
                    WHERE s.name = ? AND r.name = ?
                """, (amount, payer_name, payee_name))
                
                conn.commit()
                conn.close()
                
                # Refresh the payment screen
                self.payment_frame.destroy()
                self.create_payment_screen()
                messagebox.showinfo("Success", f"Payment processed successfully\nAmount: ${amount:.2f}\nTo: {payee_name}")
            else:
                conn.rollback()
                conn.close()
                messagebox.showerror("RTR Processing Failed", f"Payment failed: {rtr_result}")

        except Exception as e:
            logging.error(f"Transaction failed: {str(e)}")
            messagebox.showerror("Error", f"Transaction failed: {str(e)}")
            try:
                conn.rollback()
                conn.close()
            except:
                pass

if __name__ == "__main__":
    app = PaymentApp()
    app.mainloop()
