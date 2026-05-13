"""Point d'entrée de l'application."""

import sys
import tkinter as tk

from ui.login import LoginWindow
from ui.app   import PasswordManagerApp


def main() -> None:
    root = tk.Tk()
    root.withdraw()

    try:
        root.tk.call("tk", "scaling", 1.25)
    except Exception:
        pass

    login = LoginWindow(root)
    root.wait_window(login)

    if login.fernet is None or login.vault is None:
        root.destroy()
        sys.exit(0)

    root.deiconify()
    PasswordManagerApp(root, login.fernet, login.vault)
    root.mainloop()


if __name__ == "__main__":
    main()
