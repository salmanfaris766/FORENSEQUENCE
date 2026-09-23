import tkinter as tk
import ttkbootstrap as ttk

def main():
    # Initialize the app with a dark theme as a placeholder
    app = ttk.Window(themename="darkly")
    app.title("FORENSEQUENCE - Kernel Initialization")
    app.geometry("1200x760")
    
    # Simple placeholder label
    label = ttk.Label(app, text="> FORENSEQUENCE V1.0 - FILESYSTEM READY", font=("Courier", 16))
    label.pack(expand=True)
    
    app.mainloop()

if __name__ == "__main__":
    main()
