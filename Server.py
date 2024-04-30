from collections import UserList
import sys

import tkinter as tk
from tkinter import SEL, scrolledtext
from tkinter import ttk

import time
import threading
from webbrowser import get

from python_banyan.banyan_base_multi import BanyanBaseMulti
from datetime import datetime, timedelta

class MainServer(BanyanBaseMulti):
    def __init__(self, back_plane_csv_file='spec.csv', process_name='Main Server', loop_time = 0.01):
        super(MainServer, self).__init__(back_plane_csv_file=back_plane_csv_file, process_name=process_name, loop_time=loop_time)
        
        self.socket_a = self.find_socket("Server", self.PUB_SOCK)
        self.socket_b = self.find_socket("Client1", self.PUB_SOCK)
        self.socket_c = self.find_socket("Client2", self.PUB_SOCK)
        self.socket_d = self.find_socket("Client3", self.PUB_SOCK)

        threading.Thread(target=self.start_gui, daemon=True).start()
        
        try:
            self.receive_loop()
        except KeyboardInterrupt:
            self.clean_up()
            sys.exit(0)
            
    def start_gui(self):
        root = tk.Tk()
        self.app = ServerUI(root, self)
        updater.set_server_ui_instance(self.app)
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
            
    def incoming_message_processing(self, topic, payload):
        if payload['id'] == 'a':
            client = payload['id']
            if payload['func'] == 'login':
                
                username = payload['username']
                password = payload['password']

                #Verify Login
                updater.update_messages(message = f"{username}, is trying to connect...\n")
                valid_credentials = updater.is_valid_user(username, password)
                is_online = updater.is_online(username)
                valid = (valid_credentials and not is_online)
                
                if is_online == False:
                    if valid_credentials == True:
                        updater.add_online_list(username, client)
                        updater.update_messages(message = f"{username}, has connected.\n")
                        online_list = updater.show_online_list()
                        online_list = list(online_list)
                        self.publish_payload({'func': 'online_list', 'username': online_list}, self.socket_a, 'server')
                    else:
                        updater.update_messages(message = f"{username}, could not connect due to mismateched credentials.\n")
                else:
                    updater.update_messages(message = f"{username}, could not connect because user is already online\n")
                self.publish_payload({'func': 'verify', 'value': valid}, self.socket_a, 'server')
                
            if payload['func'] == 'logout':
                username = payload['username']
                updater.remove_online_list(client)
                updater.update_messages(message = f"{username}, has disconnected.\n")
                    
            if payload['func'] == 'timer':
                updater.update_messages(payload['time'])
                
            #Send To Multiple
            if payload['func'] == 'add_item_list':
               client_id = payload['id']
               item_id = payload['item_id']
               item_name = payload['item_name']
               item_price = payload['item_price']
               username = payload['username']
               updater.add_item_list(client_id, item_id, item_name, item_price)
               updater.bidding_list[client+str(item_id)] = item_price
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_a, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_b, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_c, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_d, 'server')
               
            if payload['func'] == 'bid':
                item_id = payload['item_id']
                item_name = payload['item_name']
                highest_bid = payload['bid_amount']
                username = payload['username']
                item_price = payload['item_price']
                updater.bidding_list[item_id] = ['highest_bid', highest_bid]
                self.publish_payload({'func': 'bidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_a, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_b, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_c, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_d, 'server')
                
        if payload['id'] == 'b':
            client = payload['id']
            if payload['func'] == 'login':
                
                username = payload['username']
                password = payload['password']

                #Verify Login
                updater.update_messages(message = f"{username}, is trying to connect...\n")
                valid_credentials = updater.is_valid_user(username, password)
                is_online = updater.is_online(username)
                valid = (valid_credentials and not is_online)
                
                if is_online == False:
                    if valid_credentials == True:
                        updater.add_online_list(username, client)
                        updater.update_messages(message = f"{username}, has connected.\n")
                        online_list = updater.show_online_list()
                        online_list = list(online_list)
                        self.publish_payload({'func': 'online_list', 'username': online_list}, self.socket_b, 'server')
                    else:
                        updater.update_messages(message = f"{username}, could not connect due to mismateched credentials.\n")
                else:
                    updater.update_messages(message = f"{username}, could not connect because user is already online\n")
                self.publish_payload({'func': 'verify', 'value': valid}, self.socket_b, 'server')
                
            if payload['func'] == 'logout':
                username = payload['username']
                updater.remove_online_list(client)
                updater.update_messages(message = f"{username}, has disconnected.\n")
                    
            if payload['func'] == 'timer':
                updater.update_messages(payload['time'])
                
            #Send To Multiple
            if payload['func'] == 'add_item_list':
               client_id = payload['id']
               item_id = payload['item_id']
               item_name = payload['item_name']
               item_price = payload['item_price']
               username = payload['username']
               updater.add_item_list(client_id, item_id, item_name, item_price)
               updater.bidding_list[client+str(item_id)] = item_price
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_a, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_b, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_c, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_d, 'server')
            if payload['func'] == 'bid':
                item_id = payload['item_id']
                item_name = payload['item_name']
                highest_bid = payload['bid_amount']
                username = payload['username']
                item_price = payload['item_price']
                updater.bidding_list[item_id] = ['highest_bid', highest_bid]
                self.publish_payload({'func': 'bidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_b, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_a, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_c, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_d, 'server')
                
        if payload['id'] == 'c':
            client = payload['id']
            if payload['func'] == 'login':
                
                username = payload['username']
                password = payload['password']

                #Verify Login
                updater.update_messages(message = f"{username}, is trying to connect...\n")
                valid_credentials = updater.is_valid_user(username, password)
                is_online = updater.is_online(username)
                valid = (valid_credentials and not is_online)
                
                if is_online == False:
                    if valid_credentials == True:
                        updater.add_online_list(username, client)
                        updater.update_messages(message = f"{username}, has connected.\n")
                        online_list = updater.show_online_list()
                        online_list = list(online_list)
                        self.publish_payload({'func': 'online_list', 'username': online_list}, self.socket_c, 'server')
                    else:
                        updater.update_messages(message = f"{username}, could not connect due to mismateched credentials.\n")
                else:
                    updater.update_messages(message = f"{username}, could not connect because user is already online\n")
                self.publish_payload({'func': 'verify', 'value': valid}, self.socket_c, 'server')
                
            if payload['func'] == 'logout':
                username = payload['username']
                updater.remove_online_list(client)
                updater.update_messages(message = f"{username}, has disconnected.\n")
                    
            if payload['func'] == 'timer':
                updater.update_messages(payload['time'])
                
            #Send To Multiple
            if payload['func'] == 'add_item_list':
               client_id = payload['id']
               item_id = payload['item_id']
               item_name = payload['item_name']
               item_price = payload['item_price']
               username = payload['username']
               updater.add_item_list(client_id, item_id, item_name, item_price)
               updater.bidding_list[client+str(item_id)] = item_price
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_a, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_b, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_c, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_d, 'server')
            if payload['func'] == 'bid':
                item_id = payload['item_id']
                item_name = payload['item_name']
                highest_bid = payload['bid_amount']
                username = payload['username']
                item_price = payload['item_price']
                updater.bidding_list[item_id] = ['highest_bid', highest_bid]
                self.publish_payload({'func': 'bidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_c, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_a, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_b, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_d, 'server')
 
        if payload['id'] == 'd':
            client = payload['id']
            if payload['func'] == 'login':
                
                username = payload['username']
                password = payload['password']

                #Verify Login
                updater.update_messages(message = f"{username}, is trying to connect...\n")
                valid_credentials = updater.is_valid_user(username, password)
                is_online = updater.is_online(username)
                valid = (valid_credentials and not is_online)
                
                if is_online == False:
                    if valid_credentials == True:
                        updater.add_online_list(username, client)
                        updater.update_messages(message = f"{username}, has connected.\n")
                        online_list = updater.show_online_list()
                        online_list = list(online_list)
                        self.publish_payload({'func': 'online_list', 'username': online_list}, self.socket_d, 'server')
                    else:
                        updater.update_messages(message = f"{username}, could not connect due to mismateched credentials.\n")
                else:
                    updater.update_messages(message = f"{username}, could not connect because user is already online\n")
                self.publish_payload({'func': 'verify', 'value': valid}, self.socket_d, 'server')
                
            if payload['func'] == 'logout':
                username = payload['username']
                updater.remove_online_list(client)
                updater.update_messages(message = f"{username}, has disconnected.\n")
                    
            if payload['func'] == 'timer':
                updater.update_messages(payload['time'])
                
            #Send To Multiple
            if payload['func'] == 'add_item_list':
               client_id = payload['id']
               item_id = payload['item_id']
               item_name = payload['item_name']
               item_price = payload['item_price']
               username = payload['username']
               updater.add_item_list(client_id, item_id, item_name, item_price)
               updater.bidding_list[client+str(item_id)] = item_price
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_a, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_b, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_c, 'server')
               self.publish_payload({'func': 'add_item_list', 'username': username, 'item_id': client_id + str(item_id), 'item_name': item_name, 'item_price': item_price}, self.socket_d, 'server')
            if payload['func'] == 'bid':
                item_id = payload['item_id']
                item_name = payload['item_name']
                highest_bid = payload['bid_amount']
                username = payload['username']
                item_price = payload['item_price']
                updater.bidding_list[item_id] = ['highest_bid', highest_bid]
                self.publish_payload({'func': 'bidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_d, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_a, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_b, 'server')
                self.publish_payload({'func': 'notbidder', 'item_id': item_id, 'item_name': item_name, 'starting_bid': item_price,'highest_bid': highest_bid, 'username': username}, self.socket_c, 'server')
 
 
             
    def start_server(self):
        self.publish_payload({'func': 'start', 'value': True}, self.socket_a, 'server')
        self.publish_payload({'func': 'start', 'value': True}, self.socket_b, 'server')
        self.publish_payload({'func': 'start', 'value': True}, self.socket_c, 'server')
        self.publish_payload({'func': 'start', 'value': True}, self.socket_d, 'server')
        
    def stop_server(self):
        for item_id in list(updater.start_time.keys()):
            updater.end_timer(updater.start_time[item_id]['item_name'], item_id)
        updater.update_messages("Server Closed.\n")
        self.publish_payload({'func': 'start', 'value': False}, self.socket_a, 'server')
        self.publish_payload({'func': 'start', 'value': False}, self.socket_b, 'server')
        self.publish_payload({'func': 'start', 'value': False}, self.socket_c, 'server')
        self.publish_payload({'func': 'start', 'value': False}, self.socket_d, 'server')
        

    def bidding_ended(self, item_id):
        client_id = item_id[0]
        rest_of_item_id = item_id[1:]
        
        if 'a' in client_id:
            self.publish_payload({'func': 'remove_sell_item', 'item_id': rest_of_item_id}, self.socket_a, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': client_id}, self.socket_a, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_a, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_a, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_b, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_b, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_c, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_c, 'server')

            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_d, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_d, 'server')
            
        if 'b' in client_id:
            self.publish_payload({'func': 'remove_sell_item', 'item_id': rest_of_item_id}, self.socket_b, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': client_id}, self.socket_b, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_a, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_a, 'server')

            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_b, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_b, 'server')            
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_c, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_c, 'server')

            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_d, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_d, 'server')
            
        if 'c' in client_id:
            self.publish_payload({'func': 'remove_sell_item', 'item_id': rest_of_item_id}, self.socket_c, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': client_id}, self.socket_c, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_a, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_a, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_b, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_b, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_c, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_c, 'server')

            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_d, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_d, 'server')
            
        if 'd' in client_id:
            self.publish_payload({'func': 'remove_sell_item', 'item_id': rest_of_item_id}, self.socket_d, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': client_id}, self.socket_d, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_a, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_a, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_b, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_b, 'server')
            
            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_c, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_c, 'server')

            self.publish_payload({'func': 'remove_item_list', 'item_id': rest_of_item_id}, self.socket_d, 'server')
            self.publish_payload({'func': 'bidding_winner', 'client_id': item_id}, self.socket_d, 'server')
            
class ServerUI:
    def __init__(self, root, server_instance):
        self.root = root
        self.root.title("Server UI")
        self.root.geometry("720x480")
        self.server_instance = server_instance
        self.is_dark_mode = False

        self.light_mode = {
            "bg1": "#f0f0f0",
            "bg": "#C0C0C0",
            "fg": "#000000",
            "entry_bg": "#ccc",
            "entry_fg": "black",
            "btn_bg": "#ddd",
            "btn_fg": "black",
            "start_bg": "#bbb",
        }

        self.dark_mode = {
            "bg1": "#222",
            "bg": "#333",
            "fg": "white",
            "entry_bg": "#555",
            "entry_fg": "white",
            "btn_bg": "#444",
            "btn_fg": "white",
            "start_bg": "#444",
        }

        # Frame for the main application
        self.app_frame = tk.Frame(self.root, bg=self.light_mode["bg1"])
        self.app_frame.pack(expand=True, fill="both")

        # Frame for the message window
        self.message_frame = tk.Frame(self.app_frame, bg=self.light_mode["bg"])
        self.message_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        # ScrolledText to display incoming messages
        self.message_text = scrolledtext.ScrolledText(self.message_frame, wrap=tk.WORD, width=40, height=10, bg=self.light_mode["entry_bg"], fg=self.light_mode["entry_fg"], state=tk.DISABLED)
        self.message_text.pack(expand=True, fill="both")

        # Frame for the start frame
        self.start_frame = tk.Frame(self.app_frame, bg=self.light_mode["bg"])
        self.start_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Button to switch between light and dark mode
        self.mode_button = tk.Button(self.start_frame, text="Dark Mode", command=self.toggle_mode, bg=self.light_mode["btn_bg"], fg=self.light_mode["btn_fg"])
        self.mode_button.pack(pady=10)


        self.server_timer_label = tk.Label(self.start_frame, text="Server Timer: ", bg=self.light_mode["bg"], fg=self.light_mode["fg"])
        self.server_timer_label.pack(pady=10)
        self.server_timer_entry = tk.Entry(self.start_frame, bg=self.light_mode["start_bg"])
        self.server_timer_entry.pack(pady=10)

        self.bidding_timer_label = tk.Label(self.start_frame, text="Bidding Timer: ", bg=self.light_mode["bg"], fg=self.light_mode["fg"])
        self.bidding_timer_label.pack(pady=10)
        self.bidding_timer_entry = tk.Entry(self.start_frame, bg=self.light_mode["start_bg"])
        self.bidding_timer_entry.pack(pady=10)
        
        self.start_button = tk.Button(self.start_frame, text="Start Server", command=self.start_server, bg=self.light_mode["btn_bg"], fg=self.light_mode["btn_fg"])
        self.start_button.pack(pady=10)
        
        # Frame for the online list
        self.online_list_frame = tk.Frame(self.app_frame, bg=self.light_mode["bg"])
        self.online_list_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        self.online_list_label = tk.Label(self.online_list_frame, text=f"Online List:", bg=self.light_mode["bg"], fg=self.light_mode["fg"])
        self.online_list_label.pack(pady=10)
        
        self.client_labels = []
        self.update_online_list()
            
        self.app_frame.grid_rowconfigure(0, weight=1)
        self.app_frame.grid_rowconfigure(1, weight=1)
        self.app_frame.grid_columnconfigure(0, weight=1)
        self.app_frame.grid_columnconfigure(1, weight=1)
        
    def update_online_list(self):
        for label in self.client_labels:
            label.destroy()
        for client, user in updater.show_client_online_list():
            label_text = f"{client}: {user}"
            client_label = tk.Label(self.online_list_frame, text=label_text, bg=self.light_mode["bg"], fg=self.light_mode["fg"])
            client_label.pack(pady=1)
            self.client_labels.append(client_label)
        
    def apply_theme(self, theme):
        self.app_frame.configure(bg=theme["bg1"])

        self.start_frame.configure(bg=theme["bg"])
        self.server_timer_label.configure(bg=theme["bg"], fg=theme["fg"])
        self.server_timer_entry.configure(bg=theme["start_bg"])
        self.bidding_timer_label.configure(bg=theme["bg"], fg=theme["fg"])
        self.bidding_timer_entry.configure(bg=theme["start_bg"])
        
        self.mode_button.configure(bg=theme["btn_bg"], fg=theme["btn_fg"])
        self.start_button.configure(bg=theme["btn_bg"], fg=theme["btn_fg"])
        
        self.message_frame.configure(bg=theme["bg"])
        self.message_text.configure(bg=theme["entry_bg"], fg=theme["entry_fg"])
        self.online_list_label.configure(bg=theme["bg"], fg=theme["fg"])
        self.online_list_frame.configure(bg=theme["bg"])
        
        for label in self.client_labels:
            label.configure(bg=theme["bg"], fg=theme["fg"])
            
    def toggle_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.apply_theme(self.dark_mode)
            self.mode_button["text"] = "Light Mode"
        else:
            self.apply_theme(self.light_mode)
            self.mode_button["text"] = "Dark Mode"

    def start_server(self):
        server_timer_value = self.server_timer_entry.get()
        bidding_limit_value = self.bidding_timer_entry.get()

        try:
            updater.server_timer = int(server_timer_value)
            updater.bidding_limit = int(bidding_limit_value)

            # Start the countdown for the server timer
            end_time_server = datetime.now() + timedelta(seconds=updater.server_timer)
            self.update_timer(self.server_timer_label, end_time_server)

            self.server_instance.start_server()

        except ValueError:
            print("Invalid input for server timer or bidding limit.")
            return

    def update_timer(self, label, end_time):
        remaining_time = end_time - datetime.now()
        countdown = max(remaining_time.total_seconds(), 0)

        # Update the label text with the countdown
        label["text"] = f"{label.cget('text').split(':')[0]}: {countdown:.0f} seconds"

        # If there's still time left, schedule the next update after 1000 milliseconds (1 second)
        if countdown > 0:
            self.root.after(1000, self.update_timer, label, end_time)
        else:
            self.server_instance.stop_server()
            
    def bidding_ended(self, item_id):
        self.server_instance.bidding_ended(item_id)
            
class updater():
    user_list = {
        "a": "1",
        "b": "2",
        "c": "3",
        "d": "4",
        "john": "123"
    }

    item_list = {}   
    bidding_list = {}
    bidding_limit = 0
    start_time = {}
    server_timer = None
    
    online_list = {
        }
    
    server_ui_instance = None
    
    @classmethod
    def set_server_ui_instance(cls, server_ui_instance):
        cls.server_ui_instance = server_ui_instance
        
    @classmethod
    def update_messages(cls, message):
        if cls.server_ui_instance:
            cls.server_ui_instance.message_text.config(state=tk.NORMAL)
            cls.server_ui_instance.message_text.insert(tk.END, message)
            cls.server_ui_instance.message_text.yview(tk.END)
            cls.server_ui_instance.message_text.config(state=tk.DISABLED)
    @classmethod
    def is_valid_user(cls, username, password):
        if username in cls.user_list and cls.user_list[username] == password:
            return True
        else:
            return False
        
    @classmethod
    def is_online(cls, username):
        if username in cls.online_list:
            return True
        else:
            return False

    @classmethod
    def add_online_list(cls, username, client):
        cls.online_list[username] = client

    @classmethod
    def remove_online_list(cls, client):
            keys_to_remove = [key for key, value in cls.online_list.items() if value == client]
            for key in keys_to_remove:
                del cls.online_list[key]

    @classmethod
    def show_online_list(cls):
        return list(cls.online_list.keys())

    @classmethod
    def show_client_online_list(cls):
        return cls.online_list.items()
    
    @classmethod
    def add_item_list(cls, client, item_id, name, price):
        if client not in cls.item_list:
            cls.item_list[client] = []
        new_item = {'item_id': client+str(item_id), 'item_name': name, 'item_price': price}
        cls.item_list[client].append(new_item)
        timer_thread = threading.Thread(target=updater.start_timer, args=(name, client+str(item_id)))
        timer_thread.start()
        
    @classmethod
    def show_item_list(cls, client):
        all_clients_except_current = [key for key in cls.item_list.keys() if key != client]
        combined_list = []
        for other_client in all_clients_except_current:
            combined_list += cls.item_list[other_client]
        return combined_list
     
    @classmethod
    def client_bid(cls, item_id, bid):
        if item_id in cls.item_list:
            pass
    
    @classmethod
    def start_timer(cls, name, item_id):
        if item_id in cls.start_time:
            raise ValueError(f"Timer {name} is currently running.")
        
        cls.start_time[item_id] = {
            'start_time': time.perf_counter(),
            'item_name': name
        }

        cls._check_timer(item_id)
        
    @classmethod
    def _check_timer(cls, item_id):
        while item_id in cls.start_time:
            elapsed_time = time.perf_counter() - cls.start_time[item_id]['start_time']
            duration = cls.bidding_limit

            if elapsed_time >= duration:
                cls.end_timer(cls.start_time[item_id]['item_name'], item_id)
                break
            time.sleep(1)

    @classmethod
    def end_timer(cls, name, item_id):
        cls.update_messages(f"{name} bidding has ended.\n")
        del cls.start_time[item_id]
        cls.server_ui_instance.bidding_ended(item_id)
        

if __name__ == "__main__":
    server = MainServer()
