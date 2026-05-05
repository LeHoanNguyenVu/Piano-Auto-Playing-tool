"""
RobloxPianoPlayer — Auto Piano Player for Roblox Virtual Piano

Entry point for the application.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk


def main():
    # Set appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Import and launch
    from ui.app import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
