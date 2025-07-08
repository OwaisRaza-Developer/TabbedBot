
import time
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import random
import logging
import os

# === Logging Setup ===
logging.basicConfig(filename="url_bot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# === URL Bot Class ===
class URLBot:
    def __init__(self, url, count, interval, use_proxy, chromedriver_path, status_callback):
        self.url = url
        self.count = count
        self.interval = interval
        self.use_proxy = use_proxy
        self.chromedriver_path = chromedriver_path
        self.browsers = []
        self.running = True
        self.status_callback = status_callback
        self.proxies = self.load_proxies()

        try:
            self.ua = UserAgent()
            self.status_callback("✔ User-Agent loaded from fake_useragent")
        except:
            self.ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            self.status_callback("⚠ Fallback user-agent used")

    def load_proxies(self):
        proxy_file = "proxies.txt"
        if self.use_proxy and os.path.exists(proxy_file):
            with open(proxy_file, "r") as file:
                return [line.strip() for line in file if line.strip()]
        return []

    def get_options(self, proxy=None):
        options = Options()
        options.add_argument(f"user-agent={self.ua.random}")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("detach", True)
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        return options

    def start_bot(self):
        try:
            proxy = random.choice(self.proxies) if self.use_proxy and self.proxies else None
            options = self.get_options(proxy)
            service = Service(self.chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)

            # Open first tab
            driver.get(self.url)
            self.browsers.append(driver)
            self.status_callback(f"🟢 Opened main tab using {'proxy ' + proxy if proxy else 'local IP'}")

            # Open remaining tabs
            for i in range(1, self.count):
                driver.execute_script(f"window.open('{self.url}', '_blank');")
                self.status_callback(f"🟢 Opened tab {i + 1} via JavaScript")
                time.sleep(0.5)

            threading.Thread(target=self.refresh_loop, daemon=True).start()

        except Exception as e:
            error_msg = f"❌ Startup Error: {e}"
            logging.error(error_msg)
            self.status_callback(error_msg)
            messagebox.showerror("Startup Failed", str(e))

    def refresh_loop(self):
        try:
            driver = self.browsers[0]
            while self.running:
                time.sleep(self.interval)
                handles = driver.window_handles
                for i, handle in enumerate(handles):
                    try:
                        driver.switch_to.window(handle)
                        driver.refresh()
                        msg = f"🔁 Refreshed tab {i + 1}"
                        logging.info(msg)
                        self.status_callback(msg)
                    except Exception as e:
                        logging.warning(f"Tab {i + 1} refresh failed: {e}")
        except Exception as e:
            logging.error(f"Refresh Loop Error: {e}")
            self.status_callback(f"❌ Refresh Loop Error: {e}")

    def stop_bot(self):
        self.running = False
        for driver in self.browsers:
            try:
                driver.quit()
            except:
                pass
        logging.info("Bot stopped. All tabs closed.")
        self.status_callback("🛑 Bot stopped. All tabs closed.")

# === GUI Class ===
class BotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌑 Dark Web Load Tester Bot")
        self.root.configure(bg="#1e1e1e")

        self.start_time = time.time()

        label_opts = {"bg": "#1e1e1e", "fg": "white", "font": ("Segoe UI", 10)}
        entry_opts = {"bg": "#2d2d2d", "fg": "white", "insertbackground": "white", "font": ("Segoe UI", 10)}

        # Labels and Inputs
        tk.Label(root, text="Website URL:", **label_opts).grid(row=0, column=0, sticky="e")
        self.url_entry = tk.Entry(root, width=40, **entry_opts)
        self.url_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(root, text="Tabs to Open:", **label_opts).grid(row=1, column=0, sticky="e")
        self.tabs_entry = tk.Entry(root, width=10, **entry_opts)
        self.tabs_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(root, text="Refresh Interval (sec):", **label_opts).grid(row=2, column=0, sticky="e")
        self.interval_entry = tk.Entry(root, width=10, **entry_opts)
        self.interval_entry.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(root, text="ChromeDriver Path:", **label_opts).grid(row=3, column=0, sticky="e")
        self.driver_entry = tk.Entry(root, width=40, **entry_opts)
        self.driver_entry.insert(0, "C:/webdrivers/chromedriver.exe")
        self.driver_entry.grid(row=3, column=1, padx=5, pady=2)

        self.proxy_var = tk.BooleanVar()
        self.proxy_check = tk.Checkbutton(root, text="Use Proxies (proxies.txt)", variable=self.proxy_var,
                                          bg="#1e1e1e", fg="white", selectcolor="#1e1e1e",
                                          activebackground="#1e1e1e", font=("Segoe UI", 10))
        self.proxy_check.grid(row=4, column=1, sticky="w", pady=2)

        # Buttons
        self.start_button = tk.Button(root, text="▶ Start Bot", command=self.start_bot,
                                      bg="#007acc", fg="white", font=("Segoe UI", 10))
        self.start_button.grid(row=5, column=0, pady=10)

        self.stop_button = tk.Button(root, text="■ Stop Bot", command=self.stop_bot,
                                     bg="#d9534f", fg="white", font=("Segoe UI", 10))
        self.stop_button.grid(row=5, column=1, pady=10)

        # Status box
        self.status_box = scrolledtext.ScrolledText(root, width=65, height=10,
                                                    bg="#121212", fg="#c5c5c5", font=("Consolas", 9))
        self.status_box.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
        self.status_box.insert(tk.END, "✅ Status messages will appear here...\n")
        self.status_box.config(state=tk.DISABLED)

        # Footer
        self.footer_label = tk.Label(root, text="", fg="#888", bg="#1e1e1e", font=("Segoe UI", 9, "italic"))
        self.footer_label.grid(row=7, column=0, columnspan=2, pady=(0, 5))
        self.update_footer()

        self.bot = None

    def update_footer(self):
        elapsed = int(time.time() - self.start_time)
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.footer_label.config(
            text=f"⏱ Running: {h:02d}:{m:02d}:{s:02d}   |   {timestamp}   |   ©2025 TabbedBot · Developed by OwaisRaza · All rights reserved"
        )
        self.root.after(1000, self.update_footer)


    def update_status(self, message):
        print("[STATUS]", message)
        self.status_box.config(state=tk.NORMAL)
        self.status_box.insert(tk.END, message + "\n")
        self.status_box.see(tk.END)
        self.status_box.config(state=tk.DISABLED)

    def start_bot(self):
        url = self.url_entry.get().strip()
        try:
            count = int(self.tabs_entry.get())
            interval = int(self.interval_entry.get())
            driver_path = self.driver_entry.get().strip()
        except:
            messagebox.showerror("Input Error", "Please enter valid numbers.")
            return

        if not url or not driver_path:
            messagebox.showerror("Missing Info", "Please fill all required fields.")
            return

        self.bot = URLBot(url, count, interval, self.proxy_var.get(), driver_path, self.update_status)
        self.update_status("🚀 Starting bot...")
        self.bot.start_bot()

    def stop_bot(self):
        if self.bot:
            self.update_status("🛑 Stopping bot...")
            self.bot.stop_bot()

# === Run App ===
if __name__ == "__main__":
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()
