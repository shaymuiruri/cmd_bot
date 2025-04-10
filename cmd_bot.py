import os
import sys
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import psutil
import speech_recognition as sr
import openai
from fuzzywuzzy import process
from threading import Thread

# 🛠 OpenAI API Key (Visible as requested)
OPENAI_API_KEY = "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"

# Predefined commands
commands = {
    "git status": "Shows the status of the Git repository",
    "mkdir": "Creates a new folder",
    "rmdir /s /q": "Deletes a folder",
    "ping": "Pings a website or IP address",
    "ipconfig": "Shows network configuration",
    "tasklist": "Lists all running processes",
    "taskkill /F /PID": "Forcefully kills a process by ID",
    "cls": "Clears the terminal",
    "exit": "Exits the bot",
    "cd": "Changes the current directory",
    "dir": "Lists files in the current directory",
    "echo": "Prints a message to the console",
    "copy": "Copies files from one location to another",
    "move": "Moves files from one location to another",
    "del": "Deletes files",
    "ren": "Renames a file",
    "start": "Starts a program with the provided arguments",
    "ls": "Lists files in the current directory (Unix command)",
    "pwd": "Prints the current working directory (Unix command)",
    "clear": "Clears the terminal (Unix command)",
    "touch": "Creates a new file (Unix command)",
    "rm": "Removes files or directories (Unix command)",
    "cp": "Copies files or directories (Unix command)",
    "mv": "Moves files or directories (Unix command)",
        
}

aliases = {"gst": "git status", "mk": "mkdir", "rm": "rmdir /s /q", "net": "ipconfig"}

history = []

def correct_command(input_cmd):
    """Finds the closest matching command using fuzzy matching."""
    if not input_cmd.strip():
        return input_cmd
    best_match, score = process.extractOne(input_cmd, commands.keys())
    return best_match if score > 80 else input_cmd

# System monitoring
def check_system_status():
    return psutil.cpu_percent(interval=1), psutil.virtual_memory().percent

# AI ChatGPT Integration
def ask_chatgpt(query):
    """Sends query to ChatGPT and returns response."""
    if not OPENAI_API_KEY:
        return "⚠️ OpenAI API Key is missing. Set it in your environment variables."
    
    client = openai.OpenAI(api_key=OPENAI_API_KEY)  # Use new OpenAI client

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query}]
        )
        return response.choices[0].message.content  # Adjusted response format
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Voice Command Function
def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            return "❌ Could not understand voice input."
        except sr.RequestError:
            return "⚠️ Speech service is down."

# GUI Class
class CMD_GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CMD Bot")
        self.geometry("800x600")
        self.configure(bg="#121212")
        self.create_widgets()
        self.update_system_status()

    def create_widgets(self):
        """Creates the UI elements."""
        tk.Label(self, text="Enter Command:", fg="white", bg="#121212").pack()
        
        self.command_entry = ttk.Combobox(self, width=50)
        self.command_entry.pack()
        self.command_entry.bind("<KeyRelease>", self.update_suggestions)
        self.command_entry.bind("<Return>", self.execute_command)
        
        tk.Button(self, text="🎤 Voice Command", command=self.voice_command, bg="#333", fg="white").pack()
        self.output_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=15, bg="#222", fg="white")
        self.output_area.pack()
        
        self.system_status = tk.Label(self, text="System Status", fg="white", bg="#121212")
        self.system_status.pack()
        self.cpu_label = tk.Label(self, text="CPU Usage: ", fg="white", bg="#121212")
        self.cpu_label.pack()
        self.ram_label = tk.Label(self, text="RAM Usage: ", fg="white", bg="#121212")
        self.ram_label.pack()

        tk.Button(self, text="Command History", command=self.show_history, bg="#444", fg="white").pack()
        tk.Button(self, text="Clear Output", command=self.clear_output, bg="#444", fg="white").pack()

        tk.Label(self, text="Ask ChatGPT:", fg="white", bg="#121212").pack()
        self.chat_entry = tk.Entry(self, width=50, bg="#333", fg="white")
        self.chat_entry.pack()
        self.chat_entry.bind("<Return>", self.ask_ai)
        self.chat_output = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=80, height=8, bg="#222", fg="white")
        self.chat_output.pack()

    def update_suggestions(self, event):
        """Updates command suggestions based on user input."""
        typed_text = self.command_entry.get()
        if typed_text:
            suggestions = [cmd for cmd in commands.keys() if cmd.startswith(typed_text)]
            self.command_entry["values"] = suggestions

    def execute_command(self, event=None):
        """Executes the entered command in the system shell."""
        cmd = self.command_entry.get().strip()
        if cmd in aliases:
            cmd = aliases[cmd]
        corrected_cmd = correct_command(cmd)
        if corrected_cmd != cmd:
            response = messagebox.askyesno("Command Suggestion", f"Did you mean `{corrected_cmd}`?")
            if response:
                cmd = corrected_cmd
        
        history.append(cmd)
        self.output_area.insert(tk.END, f"> {cmd}\n")
        self.output_area.see(tk.END)

        try:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            self.output_area.insert(tk.END, output.decode() if output else error.decode())
        except Exception as e:
            self.output_area.insert(tk.END, f"Error: {e}\n")
        self.command_entry.delete(0, tk.END)

    def voice_command(self):
        """Listens to a voice command and executes it."""
        voice_thread = Thread(target=self.listen_voice_command)
        voice_thread.start()

    def listen_voice_command(self):
        """Processes and executes a voice command."""
        voice_cmd = listen_command()
        self.output_area.insert(tk.END, f"🎙️: {voice_cmd}\n")
        if voice_cmd not in ["❌ Could not understand voice input.", "⚠️ Speech service is down."]:
            response = messagebox.askyesno("Execute Voice Command", f"Do you want to execute: `{voice_cmd}`?")
            if response:
                self.command_entry.insert(0, voice_cmd)
                self.execute_command()

    def ask_ai(self, event=None):
        """Sends a query to ChatGPT and displays the response."""
        query = self.chat_entry.get().strip()
        response = ask_chatgpt(query)
        self.chat_output.insert(tk.END, f"🤖: {response}\n")
        self.chat_entry.delete(0, tk.END)

    def show_history(self):
        """Displays the command execution history."""
        if history:
            messagebox.showinfo("Command History", "\n".join(history))
        else:
            messagebox.showinfo("Command History", "No commands executed yet.")    

    def clear_output(self):
        """Clears the output area."""
        self.output_area.delete("1.0", tk.END)

    def update_system_status(self):
        """Updates CPU and RAM usage stats periodically."""
        cpu, memory = check_system_status()
        self.cpu_label.config(text=f"CPU Usage: {cpu}%")
        self.ram_label.config(text=f"RAM Usage: {memory}%")
        self.after(5000, self.update_system_status)

if __name__ == "__main__":
    app = CMD_GUI()
    app.mainloop()
   