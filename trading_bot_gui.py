import tkinter as tk
from tkinter import messagebox
from threading import Thread
import logging
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from trading_bot import TradingBot

class TextHandler(logging.StreamHandler):
    def __init__(self, text):
        logging.StreamHandler.__init__(self)
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        self.text.configure(state='normal')
        self.text.insert(tk.END, msg + '\n')
        self.text.configure(state='disabled')
        self.text.yview(tk.END)

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.start_button = tk.Button(self)
        self.start_button["text"] = "Start"
        self.start_button["command"] = self.start_bot
        self.start_button.pack(side="top")

        self.stop_button = tk.Button(self)
        self.stop_button["text"] = "Stop"
        self.stop_button["command"] = self.stop_bot
        self.stop_button.pack(side="top")

        self.quit = tk.Button(self, text="QUIT", fg="red", command=self.master.destroy)
        self.quit.pack(side="bottom")

        self.text = tk.Text(self, state='disabled')
        self.text.pack(side="left", fill="y")

        scrollbar = tk.Scrollbar(self, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")

        self.text['yscrollcommand'] = scrollbar.set

        # Create a logging handler using the text widget
        handler = TextHandler(self.text)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

        # Add the handler to the root logger
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def start_bot(self):
        self.thread = Thread(target=self.run_bot)
        self.thread.start()

    def stop_bot(self):
        if self.bot:
            self.bot.stop()

    def run_bot(self):
        try:
            self.bot = TradingBot(['AAPL', 'MSFT', 'GOOG'], '<Your-API-Key>', '<Your-API-Secret>', 'https://paper-api.alpaca.markets', '2023-01-01', '2023-12-31')
            self.bot.run()
        except Exception as e:
            logging.error(str(e))

root = tk.Tk()
app = Application(master=root)
app.mainloop()
