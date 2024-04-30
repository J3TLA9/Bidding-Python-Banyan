from __future__ import unicode_literals
from audioop import add

import time
import sys
import threading
import tkinter as tk
from tkinter import DISABLED, messagebox, simpledialog, ttk

from python_banyan.banyan_base import BanyanBase


class ClientServer(BanyanBase):
    def __init__(self, topics='server', back_plane_ip_address=None, process_name='Client1'):
        self.back_plane_ip_address = back_plane_ip_address

        if topics is None:
            raise ValueError('No Topic List Was Specified.')

        super(ClientServer, self).__init__(back_plane_ip_address=back_plane_ip_address, process_name=process_name)

        for x in topics:
            self.set_subscriber_topic(x)

        # Change for each client
        self.client_id = 'a'

        threading.Thread(target=self.start_gui, daemon=True).start()

        try:
            self.receive_loop()
        except KeyboardInterrupt:
            self.clean_up()
            sys.exit(0)

    def start_gui(self):
        root = tk.Tk()
        self.app = ClientApp(root, self)
        try:
            root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

    def incoming_message_processing(self, topic, payload):
        if payload['func'] == 'verify':
            if payload['value']:
                self.app.set_logged_in(True)
            elif not payload['value']:
                self.app.frames[LoginFrame].invalid_login_widgets()
            elapsed_time = RunningTime.stop_timer("login")
            timer = f"Login Running Time: {elapsed_time:.5f}\n"
            self.publish_payload({'id': self.client_id, 'func': 'timer', 'time': timer}, 'client')

        if payload['func'] == 'start':
            if payload['value']:
                self.app.server_state(True)
            else:
                self.app.server_state(False)

        if payload['func'] == 'add_item_list':
            username = payload['username']
            item_id = payload['item_id']
            item_name = payload['item_name']
            starting_bid = payload['item_price']
            highest_bid = starting_bid
            self.app.set_item_list(item_id, item_name, starting_bid, username, highest_bid, 0)

        if payload['func'] == 'bidder':
            item_name = payload['item_name']
            item_id = payload['item_id']
            starting_bid = payload['starting_bid']
            username = payload['username']
            highest_bid = payload['highest_bid']
            self.app.set_item_list(item_id, item_name, starting_bid, username, highest_bid, 1)
            self.app.set_bidding_list(item_id, item_name, starting_bid, highest_bid)
            self.app.update_bidding_item(item_id, item_name, username, highest_bid)
            
        if payload['func'] == 'notbidder':
            item_name = payload['item_name']
            item_id = payload['item_id']
            starting_bid = payload['starting_bid']
            username = payload['username']
            highest_bid = payload['highest_bid']
            self.app.set_item_list(item_id, item_name, starting_bid, username, highest_bid, 1)
            
        if payload['func'] == 'remove_sell_item':
            pass
        if payload['func'] == 'bidding_winner':
            pass
        if payload['func'] == 'remove_item)list':
            pass
        

    def send_login(self, username, password):
        self.app.set_username(username)
        self.app.set_password(password)
        username = self.app.get_username()
        password = self.app.get_password()
        self.publish_payload({'id': self.client_id, 'func': 'login', 'username': username, 'password': password},
                             'client')

    def send_logout(self):
        username = self.app.get_username()
        self.publish_payload({'id': self.client_id, 'func': 'logout', 'username': username}, 'client')

    def send_sell_item(self, item_id, item_name, item_price):
        username = self.app.get_username()
        self.publish_payload({'id': self.client_id, 'func': 'add_item_list', 'item_id': item_id, 'item_name': item_name,
                              'item_price': item_price, 'username': username}, 'client')

    def send_bid(self, item_id, item_name, item_price, bid_amount):
        username = self.app.get_username()
        self.publish_payload(
            {'id': self.client_id, 'func': 'bid', 'item_id': item_id, 'item_name': item_name, 'item_price': item_price, 'bid_amount': bid_amount,
             'username': username}, 'client')


class RunningTime():
    start_time = {}

    @classmethod
    def start_timer(cls, name):
        if name in cls.start_time:
            raise ValueError(f"Timer {name} is currently running.")
        cls.start_time[name] = time.perf_counter()

    @classmethod
    def stop_timer(cls, name):
        if name not in cls.start_time:
            raise ValueError(f"Timer {name} has not been started.")

        elapsed_time = time.perf_counter() - cls.start_time[name]
        del cls.start_time[name]
        return elapsed_time


class ClientApp:
    def __init__(self, root, client_server_instance):
        self.root = root
        self.root.title("Client App")
        self.root.geometry("1480x720")
        self.root.minsize(920, 620)
        self.client_server_instance = client_server_instance

        # Set Frame Customize
        self.container = tk.Frame(self.root, height=480, width=240)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Initialize
        self.logged_in = False
        self.username = None
        self.password = None
        self.frames = {}
        self.inventory = {}
        self.selling_list = {}
        self.item_list = {}
        self.bidding_list = {}
        self.item_id_counter = 0

        # Get Frame Customize
        for i in (LoginFrame, MainFrame):
            frame = i(self.container, self, self.client_server_instance)
            self.frames[i] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame()

    def show_frame(self):
        if self.logged_in:
            self.root.title(f'Client {self.username}')
            frame = self.frames[MainFrame]
        else:
            self.root.title("Client App")
            frame = self.frames[LoginFrame]

        frame.tkraise()

    def set_username(self, username):
        self.username = username

    def set_password(self, password):
        self.password = password

    def set_logged_in(self, value):
        self.logged_in = value
        self.show_frame()

    def set_inventory(self, new):
        self.inventory.update(new)

    def set_item_list(self, item_id, item_name, starting_bid, username, highest_bid, value):
        if value == 0:
            message = f"{username} is selling {item_name}\n"
            self.EventTextBox.config(state=tk.NORMAL)
            self.EventTextBox.insert(tk.END, message)
            self.EventTextBox.yview(tk.END)
            self.EventTextBox.config(state=tk.DISABLED)
        self.item_list[item_id] = {'item_name': item_name, 'starting_bid': starting_bid, 'highest_bid': highest_bid}

    def set_bidding_list(self, item_id, item_name, starting_bid, highest_bid):
        self.bidding_list[item_id] = {'item_id': item_id,'item_name': item_name, 'starting_bid': starting_bid, 'highest_bid': highest_bid}
        
    def update_bidding_item(self, item_id, item_name, highest_bidder, highest_bid):
        message = f"Bid on {item_name} - Highest Bidder: {highest_bidder}, Highest Bid: ₱{highest_bid:.2f}\n"
        self.EventTextBox.config(state=tk.NORMAL)
        self.EventTextBox.insert(tk.END, message)
        self.EventTextBox.yview(tk.END)
        self.EventTextBox.config(state=tk.DISABLED)
        for item_id, item_info in self.bidding_list.items():
            self.frames[MainFrame].update_bidding_tree(item_id, item_info)

    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

    def get_logged_in(self):
        return self.logged_in

    def get_inventory(self):
        return self.inventory

    def get_item_list(self):
        return self.item_list
    
    def get_bidding_list(self):
        return self.bidding_list

    def add_new_sell_item(self, item_name, item_price):
        self.selling_list[self.item_id_counter] = {'item_name': item_name, 'item_price': item_price}
        self.client_server_instance.send_sell_item(self.item_id_counter, item_name, item_price)
        del self.inventory[item_name]
        tree = self.frames[MainFrame].SellingTree
        tree.insert("", "end", values=(self.item_id_counter, item_name, "₱{:.2f}".format(item_price)))
        self.item_id_counter += 1

    def server_state(self, value):
        if value:
            self.frames[MainFrame].InventoryButton.config(state=tk.NORMAL)
            self.frames[MainFrame].ItemListButton.config(state=tk.NORMAL)
        else:
            self.frames[MainFrame].InventoryButton.config(state=tk.DISABLED)
            self.frames[MainFrame].ItemListButton.config(state=tk.DISABLED)


class MainFrame(tk.Frame):
    def __init__(self, parent, controller, client_server_instance):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.client_server_instance = client_server_instance

        # STYLE TEST (idk if this works everytime)
        frame_style = {"bg": "white", "bd": 2, "relief": "groove", "pady": 5, "padx": 5}
        label_style = {"font": ("Arial", 12), "bg": "lightgray", "pady": 5, "padx": 5}
        button_style = {"font": ("Arial", 10), "bg": "lightblue", "pady": 5, "padx": 5}
        tree_style = {"height": 10, "columns": ("Index", "Item Name", "Price"), "show": "headings"}

        # Event Frame
        EventFrame = tk.Frame(self, width=300, height=self.winfo_reqheight(), **frame_style)
        EventFrame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)

        EventLabel = tk.Label(EventFrame, text="EVENT NOTIFICATION", **label_style)
        EventLabel.pack(fill="both", expand=True, padx=5, pady=5)

        self.controller.EventTextBox = tk.Text(EventFrame, state=tk.DISABLED)
        self.controller.EventTextBox.pack(fill="both", expand=True, padx=5, pady=5)

        LogoutButton = tk.Button(EventFrame, text="Logout", command=self.logout, **button_style)
        LogoutButton.pack(side=tk.BOTTOM, anchor=tk.SE, padx=5, pady=5)

        # Inventory Frame
        InventoryFrame = tk.Frame(self, width=200, height=self.winfo_reqheight(), **frame_style)
        InventoryFrame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.InventoryButton = tk.Button(InventoryFrame, text="INVENTORY", command=self.open_inventory_window,
                                    **button_style, state=tk.DISABLED)
        self.InventoryButton.pack(fill="both", expand=True, padx=5, pady=5)

        InventoryTreeFrame = tk.Frame(InventoryFrame)
        InventoryTreeFrame.pack(fill="both", expand=True, padx=5, pady=5)

        SellingLabel = tk.Label(InventoryTreeFrame, text="Items Your SELLING", **label_style)
        SellingLabel.pack(fill="both", expand=True, padx=5, pady=5)

        SellingTree = ttk.Treeview(InventoryTreeFrame, **tree_style)
        for col in ("Index", "Item Name", "Price"):
            SellingTree.heading(col, text=col)
        SellingTree.pack(fill="both", expand=True, padx=5, pady=5)
        self.SellingTree = SellingTree
        
        # Item List Frame
        ItemListFrame = tk.Frame(self, width=200, height=150, **frame_style)
        ItemListFrame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.ItemListButton = tk.Button(ItemListFrame, text="ITEM LIST", **button_style, command=self.open_item_list_window, state=tk.DISABLED)
        self.ItemListButton.pack(fill="both", expand=True, padx=5, pady=5)

        ItemListTreeFrame = tk.Frame(ItemListFrame)
        ItemListTreeFrame.pack(side=tk.BOTTOM, anchor=tk.SE, fill="both", expand=True)

        BiddingLabel = tk.Label(ItemListTreeFrame, text="Items Your BIDDING", **label_style)
        BiddingLabel.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("Item Name", "Current Highest Bid")
        BiddingTree = ttk.Treeview(ItemListTreeFrame, columns=columns, show="headings")
        for col in columns:
            BiddingTree.heading(col, text=col)
        BiddingTree.pack(fill="both", expand=True, padx=5, pady=5)
        self.BiddingTree = BiddingTree
        
        # Expand Proportionally
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Configure row and column weights for proportional expansion
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

    def logout(self):
        self.controller.client_server_instance.app.set_logged_in(False)
        self.client_server_instance.send_logout()

    def open_inventory_window(self):
        inventory_window = InventoryWindow(self.controller.client_server_instance.app.root, self.controller)
        self.controller.client_server_instance.app.root.protocol("WM_DELETE_WINDOW", inventory_window.destroy)
        inventory_window.transient(self.controller.client_server_instance.app.root)
        inventory_window.grab_set()
        inventory_window.focus_set()

    def open_item_list_window(self):
        self.item_list_window = ItemListWindow(self.controller.client_server_instance.app.root, self.controller,
                                               self.client_server_instance)
        self.controller.client_server_instance.app.root.protocol("WM_DELETE_WINDOW", self.item_list_window.destroy)
        self.item_list_window.transient(self.controller.client_server_instance.app.root)
        self.item_list_window.grab_set()
        self.item_list_window.focus_set()
        
    def update_bidding_tree(self, item_id, item_info):
        item_name = item_info['item_name']
        highest_bid = item_info['highest_bid']

        for child in self.BiddingTree.get_children():
            values = self.BiddingTree.item(child, 'values')
            if values and values[0] == item_id:
                new_values = (item_name, f"Highest Bid: ₱{highest_bid:.2f}")
                self.BiddingTree.item(child, values=new_values)
                return
        self.BiddingTree.insert("", "end", values=(item_name, f"Highest Bid: ₱{highest_bid:.2f}"))


class ItemListWindow(tk.Toplevel):
    def __init__(self, parent, controller, client_server_instance):
        tk.Toplevel.__init__(self, parent)
        self.controller = controller
        self.client_server_instance = client_server_instance
        self.title("Item List Window")
        self.items = self.controller.client_server_instance.app.get_item_list()
        self.index_counter = 0
        self.create_widgets()
        self.center_window()

    def center_window(self):
        main_window_width = self.controller.client_server_instance.app.root.winfo_width()
        main_window_height = self.controller.client_server_instance.app.root.winfo_height()
        x_position = (main_window_width - self.winfo_reqwidth()) // 2
        y_position = (main_window_height - self.winfo_reqheight()) // 2
        self.geometry(f"+{x_position}+{y_position}")

    def create_widgets(self):
        columns = ("Item ID", "Item Name", "Starting Bid", "Highest Bid")
        self.ItemTreeList = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.ItemTreeList.heading(col, text=col)
        self.ItemTreeList.pack(expand=True, fill=tk.BOTH)

        for item_id, item_info in self.items.items():
            item_name = item_info['item_name']
            starting_bid = item_info['starting_bid']
            highest_bid = item_info['highest_bid']

            bid_button = tk.Button(self, text="Bid", command=lambda id=item_id: self.bid_on_item(id))
            self.ItemTreeList.insert("", "end", values=(item_id, item_name, starting_bid, highest_bid))
        
        bid_button = tk.Button(self, text="Bid on Selected Item", command=self.bid_on_selected_item)
        bid_button.pack(pady=10)

    def bid_on_selected_item(self):
        selected_item = self.ItemTreeList.selection()
        if selected_item:
            values = self.ItemTreeList.item(selected_item, 'values')
            item_id, item_name, starting_bid, current_highest_bid = values

            bid_dialog = BidDialog(self, item_name)
            self.wait_window(bid_dialog)

            bid_amount_str = bid_dialog.get_bid_amount()

            if bid_amount_str is not None and bid_amount_str.strip():
                try:
                    bid_amount = float(bid_amount_str)
                    self.process_bid(item_id, item_name, starting_bid, current_highest_bid, bid_amount)
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            else:
                print("Bid amount cannot be empty.")

    def process_bid(self, item_id, item_name, starting_bid, current_highest_bid, bid_amount_str):
        try:
            bid_amount = float(bid_amount_str)
            if bid_amount >= float(starting_bid) + 0.01:
                if bid_amount > float(current_highest_bid):
                    self.client_server_instance.send_bid(item_id, item_name, starting_bid, bid_amount)
                    # Send To Main Frame Tree
                else:
                    print("Your bid must be higher than the current highest bid.")
            else:
                print("Bid amount must be greater than or equal to the minimum bid.")
        except ValueError:
            print("Invalid input. Please enter a valid number for the bid amount.")

    def update_tree(self, item_id, new_bid):
        for child in self.ItemTreeList.get_children():
            values = self.ItemTreeList.item(child, 'values')
            if values and values[0] == item_id:
                new_values = (item_id, values[1], values[2], "₱{:.2f}".format(new_bid))
                self.ItemTreeList.item(child, values=new_values)
                break


class BidDialog(tk.Toplevel):
    def __init__(self, parent, item_name):
        super().__init__(parent)
        self.result = tk.StringVar()
        self.title(f"Enter Bid for {item_name}")

        tk.Label(self, text=f"Enter your bid for {item_name}:").pack(padx=10, pady=5)
        self.entry_bid = tk.Entry(self, textvariable=self.result)
        self.entry_bid.pack(padx=10, pady=5)

        tk.Button(self, text="Bid", command=self.submit_bid).pack(padx=10, pady=5)

    def submit_bid(self):
        try:
            bid_amount = float(self.result.get())
            if bid_amount >= 0:
                self.destroy()
            else:
                messagebox.showerror("Invalid Bid", "Bid amount must be a non-negative number.")
        except ValueError:
            messagebox.showerror("Invalid Bid", "Invalid input. Please enter a valid number.")

    def get_bid_amount(self):
        return self.result.get()

class InventoryWindow(tk.Toplevel):
    def __init__(self, parent, controller):
        tk.Toplevel.__init__(self, parent)
        self.controller = controller
        self.title("Inventory Window")
        self.items = self.controller.client_server_instance.app.get_inventory()
        self.index_counter = 0
        self.create_widgets()
        self.center_window()

    def center_window(self):
        # Get the width and height of the main window
        main_window_width = self.controller.client_server_instance.app.root.winfo_width()
        main_window_height = self.controller.client_server_instance.app.root.winfo_height()

        # Calculate the center coordinates for the popup window
        x_position = (main_window_width - self.winfo_reqwidth()) // 2
        y_position = (main_window_height - self.winfo_reqheight()) // 2

        # Set the position of the popup window
        self.geometry(f"+{x_position}+{y_position}")

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("Index", "Item Name", "Price"), show="headings")
        self.tree.heading("Index", text="Index")
        self.tree.heading("Item Name", text="Item Name")
        self.tree.heading("Price", text="Price", anchor="center")

        # Set the anchor option for the text in the cells
        for col in ("Index", "Item Name", "Price"):
            self.tree.column(col, anchor="center")

        # Insert items with correct index
        index_counter = 0
        for item_name, item_price in self.items.items():
            self.tree.insert("", "end", values=(index_counter, item_name, "₱{:.2f}".format(item_price)))
            index_counter += 1

        self.tree.pack(expand=True, fill=tk.BOTH)

        sell_selected_item_button = tk.Button(self, text="Sell Selected Item", command=self.sell_selected_item)
        sell_selected_item_button.pack(pady=10)

        new_item_button = tk.Button(self, text="New Item", command=self.new_item)
        new_item_button.pack(pady=10)

    def sell_selected_item(self):
        selected_item = self.tree.selection()
        if selected_item:
            # Get index of the selected row
            selected_item_index = self.tree.index(selected_item)

            # Get values of the selected row
            values = self.tree.item(selected_item, 'values')
            item_name, item_price = values[1], float(values[2].replace('₱', ''))

            # Remove the item from the tree
            self.tree.delete(selected_item)

            # Update indices in the tree
            for i, child in enumerate(self.tree.get_children()):
                self.tree.item(child, values=(i,) + self.tree.item(child, 'values')[1:])

            # Send item details to MainFrame
            self.controller.client_server_instance.app.add_new_sell_item(item_name, item_price)

    def new_item(self):
        new_item_dialog = NewItemDialog(self)
        if new_item_dialog.result:
            new_item_name, new_item_price = new_item_dialog.result
            self.tree.insert("", "end", values=(self.index_counter, new_item_name, "₱{:.2f}".format(new_item_price)))
            self.items[new_item_name] = new_item_price
            self.index_counter += 1


class NewItemDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Item Name:").grid(row=0)
        tk.Label(master, text="Item Price:").grid(row=1)

        self.item_name_entry = tk.Entry(master)
        self.item_price_entry = tk.Entry(master)

        self.item_name_entry.grid(row=0, column=1)
        self.item_price_entry.grid(row=1, column=1)

        return self.item_name_entry

    def apply(self):
        item_name = self.item_name_entry.get()
        item_price_str = self.item_price_entry.get()

        try:
            item_price = float(item_price_str)
            self.result = (item_name, item_price)
        except ValueError:
            messagebox.showerror("Error", "Invalid price. Please enter a valid number.")
            self.result = None


class LoginFrame(tk.Frame):
    def __init__(self, parent, controller, client_server_instance):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.client_server_instance = client_server_instance
        self.label_error = None
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", font=("Arial", 15), background="#f0f0f0")
        style.configure("TEntry", font=("Arial", 12), padding=5)
        style.configure("TButton", font=("Arial", 12), padding=8)

        frame = ttk.Frame(self, style="TFrame")
        frame.pack(expand=True)

        label = ttk.Label(frame, text="LOGIN", style="TLabel")
        label.grid(row=0, column=0, columnspan=2, pady=(10, 20))

        self.username_label = ttk.Label(frame, text="Username:", style="TLabel")
        self.username_entry = ttk.Entry(frame, style="TEntry")
        self.password_label = ttk.Label(frame, text="Password:", style="TLabel")
        self.password_entry = ttk.Entry(frame, show="*", style="TEntry")
        self.login_button = ttk.Button(frame, text="Login", command=self.login, style="TButton")

        self.username_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.username_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.password_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.password_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.login_button.grid(row=3, column=0, columnspan=2, pady=10)

    def invalid_login_widgets(self):
        if self.label_error:
            self.label_error.destroy()
        self.label_error = tk.Label(self, text="Invalid, Try Again.", fg="red")
        self.label_error.pack(pady=5)
        self.after(5000, self.label_error.destroy)

    def login(self):
        self.login_button.config(state=tk.DISABLED)
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.client_server_instance.send_login(username, password)
        RunningTime.start_timer("login")
        self.after(250, self.login_button.config(state=tk.NORMAL))


def activate():
    ClientServer()


if __name__ == "__main__":
    activate()
