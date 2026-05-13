import tkinter as tk
from tkinter import ttk
from cryptography.fernet import Fernet

import vault as vault_module


class LoginWindow(tk.Toplevel):

    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.parent = parent
        self.fernet: Fernet | None = None
        self.vault: vault_module.Vault | None = None

        self._first_launch = not vault_module.vault_exists()

        self.title("Authentification")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._center()

    def _build_ui(self) -> None:
        pad = {"padx": 14, "pady": 6}
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        if self._first_launch:
            title     = "Première utilisation — création du coffre"
            btn_label = "Créer le coffre"
        else:
            title     = "Déverrouiller le coffre"
            btn_label = "Ouvrir"

        ttk.Label(frame, text=title, font=("", 11, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 14))

        ttk.Label(frame, text="Mot de passe d'accès :").grid(row=1, column=0, sticky="w", **pad)
        self._access_var = tk.StringVar()
        self._access_entry = ttk.Entry(frame, textvariable=self._access_var, show="●", width=28)
        self._access_entry.grid(row=1, column=1, **pad)
        self._access_entry.bind("<Return>", lambda _: self._next_focus(self._access_entry))

        if self._first_launch:
            ttk.Label(frame, text="Confirmer le mot de passe :").grid(row=2, column=0, sticky="w", **pad)
            self._access_confirm_var = tk.StringVar()
            self._access_confirm_entry = ttk.Entry(frame, textvariable=self._access_confirm_var, show="●", width=28)
            self._access_confirm_entry.grid(row=2, column=1, **pad)

        enc_row = 3 if self._first_launch else 2
        ttk.Label(frame, text="Clé de chiffrement :").grid(row=enc_row, column=0, sticky="w", **pad)
        self._enc_var = tk.StringVar()
        self._enc_entry = ttk.Entry(frame, textvariable=self._enc_var, show="●", width=28)
        self._enc_entry.grid(row=enc_row, column=1, **pad)
        self._enc_entry.bind("<Return>", lambda _: self._submit())

        if self._first_launch:
            ttk.Label(frame, text="Confirmer la clé :").grid(row=4, column=0, sticky="w", **pad)
            self._enc_confirm_var = tk.StringVar()
            ttk.Entry(frame, textvariable=self._enc_confirm_var, show="●", width=28).grid(row=4, column=1, **pad)

        self._error_label = ttk.Label(frame, text="", foreground="#c0392b")
        self._error_label.grid(row=10, column=0, columnspan=2, pady=(8, 0))

        ttk.Button(frame, text=btn_label, command=self._submit).grid(
            row=11, column=0, columnspan=2, pady=(10, 0))

        self._access_entry.focus()

    def _next_focus(self, current: ttk.Entry) -> None:
        current.tk_focusNext().focus()

    def _center(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _submit(self) -> None:
        access_pw = self._access_var.get()
        enc_key   = self._enc_var.get()

        if not access_pw or not enc_key:
            self._show_error("Tous les champs sont obligatoires.")
            return

        if self._first_launch:
            self._create(access_pw, enc_key)
        else:
            self._unlock(access_pw, enc_key)

    def _create(self, access_pw: str, enc_key: str) -> None:
        if access_pw != self._access_confirm_var.get():
            self._show_error("Les mots de passe d'accès ne correspondent pas.")
            return
        if enc_key != self._enc_confirm_var.get():
            self._show_error("Les clés de chiffrement ne correspondent pas.")
            return
        if len(access_pw) < 6:
            self._show_error("Mot de passe d'accès trop court (6 caractères min.).")
            return

        v, f = vault_module.create_vault(access_pw, enc_key)
        self.vault, self.fernet = v, f
        self.destroy()

    def _unlock(self, access_pw: str, enc_key: str) -> None:
        try:
            v, f = vault_module.unlock_vault(access_pw, enc_key)
            self.vault, self.fernet = v, f
            self.destroy()
        except ValueError as e:
            self._show_error(str(e))

    def _show_error(self, msg: str) -> None:
        self._error_label.config(text=msg)

    def _on_close(self) -> None:
        self.parent.destroy()
