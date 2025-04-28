import tkinter.messagebox as messagebox
import customtkinter as ctk
import sqlite3
from ISO20022_Pacs008_Generator import (
    get_all_users,
    get_user_by_name,
    generate_iso20022_message,
    save_message,
    process_through_rtr
)
from db_manager import reset_db

# === Setup customtkinter ===
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")  

class PaymentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RTR Payment Simulation")
        self.geometry("800x600")  # Larger window
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

        # Header section
        header_frame = ctk.CTkFrame(self.payment_frame)
        header_frame.pack(fill="x", padx=20, pady=(20, 30))

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
        form_frame = ctk.CTkFrame(self.payment_frame)
        form_frame.pack(fill="x", padx=100, pady=20)

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

        # Process payment
        try:
            conn = sqlite3.connect('payment_system.db')
            cursor = conn.cursor()
            
            # Only log transaction
            cursor.execute("""
                INSERT INTO transactions (sender_id, receiver_id, amount)
                SELECT s.id, r.id, ?
                FROM users s, users r
                WHERE s.name = ? AND r.name = ?
            """, (amount, payer_name, payee_name))
            
            conn.commit()

            # Generate and save ISO20022 message
            tree = generate_iso20022_message(payer, payee, amount)
            filename = save_message(tree, payer_name, payee_name)

            # Process through RTR Exchange (this will handle the actual balance updates)
            rtr_result = process_through_rtr(filename)
            
            if "Success" in rtr_result:
                conn.close()
                # First refresh the payment screen
                self.payment_frame.destroy()
                self.create_payment_screen()
                # Then show the success message
                messagebox.showinfo("Success", f"Payment processed successfully\nAmount: ${amount:.2f}\nTo: {payee_name}")
            else:
                # Rollback on RTR failure
                conn.rollback()
                conn.close()
                messagebox.showerror("RTR Processing Failed", f"Payment failed: {rtr_result}")

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Transaction failed: {str(e)}")
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    app = PaymentApp()
    app.mainloop()
