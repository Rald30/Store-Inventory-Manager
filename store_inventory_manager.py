import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import json
import os
import matplotlib.pyplot as plt
import sys

APP_FOLDER_NAME = "StoreInventoryData"

if getattr(sys, 'frozen', False):  # If running as exe
    BASE_DIR = os.path.dirname(sys.executable)
else:  # If running as py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR = os.path.join(BASE_DIR, APP_FOLDER_NAME)
os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(os.path.join(APP_DIR, "logs"), exist_ok=True)

SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

# === Files inside app folder ===
DATA_FILE = os.path.join(APP_DIR, "inventory_data.json")
LOG_FILE = os.path.join(APP_DIR, "logs", "inventory_log.txt")

class StoreInventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🛍️ Store Inventory Manager")
        self.root.geometry("950x650")
        self.root.configure(bg="#000000")

        self.items = []
        self.sold_items = []
        self.total_income = 0.0
        self.restock_reminders = set()

        self.owner_password = None
        self.load_settings()

        self.create_widgets()
        self.load_data()

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            self.owner_password = simpledialog.askstring("Set Owner Password", "Create a new owner password:", show="*", parent=self.root)
            if not self.owner_password:
                messagebox.showerror("Error", "Password cannot be empty. Exiting.", parent=self.root)
                self.root.destroy()
                return
            self.save_settings(self.owner_password)
        else:
            with open(SETTINGS_FILE, "r") as f:
                self.owner_password = json.load(f).get("owner_password", "")

    def save_settings(self, password):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"owner_password": password}, f)

    def create_widgets(self):
        title = tk.Label(self.root, text="🛍️ Store Inventory Manager", font=("Times New Roman", 20, "bold"), bg="#000000", fg="#ffffff")
        title.pack(pady=10)

        entry_frame = tk.Frame(self.root, bg="#000000")
        entry_frame.pack()

        self.name_entry = self.make_entry(entry_frame, "Name:", 0)
        self.price_entry = self.make_entry(entry_frame, "Price:", 1)
        self.qty_entry = self.make_entry(entry_frame, "Quantity:", 2)
        self.cat_entry = self.make_entry(entry_frame, "Category:", 3)

        btn_frame = tk.Frame(self.root, bg="#000000")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Add", font=("Times New Roman", 10), command=self.add_item, bg="#4CAF50", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Edit", font=("Times New Roman", 10), command=self.edit_item, bg="#FFC107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete", font=("Times New Roman", 10), command=self.delete_item, bg="#F44336", fg="white").grid(row=0, column=2, padx=5)

        self.sell_qty = tk.Entry(btn_frame, width=5)
        self.sell_qty.grid(row=0, column=3, padx=2)
        self.sell_qty.insert(0, "1")
        tk.Button(btn_frame, text="Sell", font=("Times New Roman", 10), command=self.sell_item, bg="#9C27B0", fg="white").grid(row=0, column=4, padx=5)
        tk.Button(btn_frame, text="View Log", font=("Times New Roman", 10), command=self.view_log, bg="#2196F3", fg="white").grid(row=0, column=5, padx=5)
        tk.Button(btn_frame, text="Chart", font=("Times New Roman", 10), command=self.show_chart, bg="#00BCD4", fg="white").grid(row=0, column=6, padx=5)
        tk.Button(btn_frame, text="Reset Income", font=("Times New Roman", 10), command=self.reset_income, bg="#e91e63", fg="white").grid(row=0, column=7, padx=5)
        tk.Button(btn_frame, text="Change Password", font=("Times New Roman", 10), command=self.change_password, bg="#607d8b", fg="white").grid(row=0, column=8, padx=5)

        search_frame = tk.Frame(self.root, bg="#000000")
        search_frame.pack(pady=5)
        tk.Label(search_frame, text="Search:", font=("Times New Roman", 12), bg="#00f2ff").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_search)
        tk.Entry(search_frame, textvariable=self.search_var, font=("Times New Roman", 12), width=30).pack(side="left", padx=5)

        self.tree = ttk.Treeview(self.root, columns=("Name", "Price", "Qty", "Category"), show="headings", height=10)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(pady=10, fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Times New Roman", 12, "bold"), background="#00f2ff", foreground="black")
        style.configure("Treeview", font=("Times New Roman", 12), rowheight=30,)

        self.income_label = tk.Label(self.root, text="Total Income: ₱0.00", font=("Times New Roman", 16, "bold"), bg="#000000", fg="#00ff11")
        self.income_label.pack(pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def make_entry(self, parent, text, col):
        tk.Label(parent, text=text, font=("Times New Roman", 12), bg="#00f2ff").grid(row=0, column=col*2, padx=2)
        entry = tk.Entry(parent, font=("Times New Roman", 12), width=15)
        entry.grid(row=0, column=col*2+1, padx=2)
        return entry

    def add_item(self):
        name = self.name_entry.get().strip()
        try:
            price = float(self.price_entry.get().strip())
            qty = int(self.qty_entry.get().strip())
        except:
            return messagebox.showerror("Error", "Price must be float and quantity must be int", parent=self.root)
        category = self.cat_entry.get().strip()

        if not all([name, category]):
            return messagebox.showerror("Error", "Fill all fields", parent=self.root)

        self.items.append({'name': name, 'price': price, 'qty': qty, 'category': category})
        self.tree.insert("", "end", values=(name, f"{price:.2f}", qty, category))
        self.log(f"Added {name}, Price: ₱{price}, Qty: {qty}, Category: {category}")
        self.save_data()
        self.clear_entries()

    def edit_item(self):
        selected = self.tree.selection()
        if not selected: return

        index = self.tree.index(selected[0])
        try:
            price = float(self.price_entry.get().strip())
            qty = int(self.qty_entry.get().strip())
        except:
            return messagebox.showerror("Error", "Invalid input", parent=self.root)
        item = {
            'name': self.name_entry.get().strip(),
            'price': price,
            'qty': qty,
            'category': self.cat_entry.get().strip()
        }
        self.items[index] = item
        self.tree.item(selected[0], values=(item['name'], f"{item['price']:.2f}", item['qty'], item['category']))
        self.log(f"Edited {item['name']}")
        self.save_data()
        self.clear_entries()

    def delete_item(self):
        selected = self.tree.selection()
        if not selected: return
        index = self.tree.index(selected[0])
        item = self.items.pop(index)
        self.tree.delete(selected[0])
        self.log(f"Deleted {item['name']}")
        self.save_data()

    def sell_item(self):
        selected = self.tree.selection()
        if not selected: return
        try:
            qty_to_sell = int(self.sell_qty.get())
        except:
            return messagebox.showerror("Error", "Invalid quantity to sell", parent=self.root)

        index = self.tree.index(selected[0])
        item = self.items[index]
        if qty_to_sell <= 0 or qty_to_sell > item["qty"]:
            return messagebox.showerror("Error", "Invalid quantity", parent=self.root)

        item["qty"] -= qty_to_sell
        total = item["price"] * qty_to_sell
        self.total_income += total
        self.income_label.config(text=f"Total Income: ₱{self.total_income:.2f}")
        self.log(f"Sold {qty_to_sell} of {item['name']} - Earned: ₱{total:.2f}")
        self.sold_items.append({'name': item['name'], 'qty': qty_to_sell})

        if item["qty"] == 0:
            self.tree.delete(selected[0])
            self.items.pop(index)
        else:
            self.tree.item(selected[0], values=(item['name'], f"{item['price']:.2f}", item['qty'], item['category']))
        if item["qty"] < 5 and item["name"] not in self.restock_reminders:
            messagebox.showinfo("Restock Alert", f"{item['name']} is low on stock!", parent=self.root)
            self.restock_reminders.add(item["name"])
        self.save_data()

    def view_log(self):
        win = tk.Toplevel(self.root)
        win.title("Inventory Log")
        win.geometry("500x400")
        txt = tk.Text(win)
        txt.pack(expand=True, fill="both")
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            txt.insert("1.0", f.read())

    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")

    def update_search(self, *args):
        keyword = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for item in self.items:
            if keyword in item['name'].lower():
                self.tree.insert('', 'end', values=(item['name'], f"{item['price']:.2f}", item['qty'], item['category']))

    def show_chart(self):
        if not self.sold_items:
            return messagebox.showinfo("No Sales", "No items have been sold yet.", parent=self.root)

        sold_count = {}
        for item in self.sold_items:
            name = item['name']
            qty = item['qty']
            sold_count[name] = sold_count.get(name, 0) + qty

        sorted_items = sorted(sold_count.items(), key=lambda x: x[1], reverse=True)
        names, qtys = zip(*sorted_items)

        plt.figure(figsize=(10, 6))
        bars = plt.bar(names, qtys, color='skyblue')
        plt.xlabel("Item Names")
        plt.ylabel("Total Sold Units")
        plt.title("Sold Item Report (All Sold Items)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        for bar, qty in zip(bars, qtys):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(qty), ha='center', va='bottom', fontsize=9)

        plt.show()

    def clear_entries(self):
        for entry in [self.name_entry, self.price_entry, self.qty_entry, self.cat_entry]:
            entry.delete(0, tk.END)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], 'values')
            self.name_entry.delete(0, tk.END)
            self.price_entry.delete(0, tk.END)
            self.qty_entry.delete(0, tk.END)
            self.cat_entry.delete(0, tk.END)
            self.name_entry.insert(0, values[0])
            self.price_entry.insert(0, values[1])
            self.qty_entry.insert(0, values[2])
            self.cat_entry.insert(0, values[3])

    def reset_income(self):
        password = simpledialog.askstring("Authentication Required", "Enter Owner Password:", show="*", parent=self.root)
        if password == self.owner_password:
            self.total_income = 0.0
            self.income_label.config(text="Total Income: ₱0.00")
            self.log("Total income has been reset by owner.")
            self.save_data()
        else:
            messagebox.showerror("Access Denied", "Incorrect password.", parent=self.root)

    def change_password(self):
        current = simpledialog.askstring("Change Password", "Enter current password:", show="*", parent=self.root)
        if current != self.owner_password:
            return messagebox.showerror("Error", "Incorrect current password.", parent=self.root)

        new_pw = simpledialog.askstring("New Password", "Enter new password:", show="*", parent=self.root)
        if not new_pw:
            return messagebox.showwarning("Warning", "Password cannot be empty.", parent=self.root)

        confirm = simpledialog.askstring("Confirm Password", "Confirm new password:", show="*", parent=self.root)
        if new_pw != confirm:
            return messagebox.showerror("Error", "Passwords do not match.", parent=self.root)

        self.owner_password = new_pw
        self.save_settings(new_pw)
        self.log("Owner password was changed.")
        messagebox.showinfo("Success", "Password changed successfully.", parent=self.root)

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"items": self.items, "income": self.total_income, "sold_items": self.sold_items}, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.items = data.get("items", [])
                self.total_income = data.get("income", 0.0)
                self.sold_items = data.get("sold_items", [])
                self.income_label.config(text=f"Total Income: ₱{self.total_income:.2f}")
                for item in self.items:
                    self.tree.insert('', 'end', values=(item['name'], f"{item['price']:.2f}", item['qty'], item['category']))


if __name__ == "__main__":
    root = tk.Tk()
    app = StoreInventoryApp(root)
    root.mainloop()