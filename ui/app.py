"""Fenêtre principale : onglets Ajouter, Rechercher, Liste."""

import tkinter as tk
from tkinter import ttk, messagebox
from cryptography.fernet import Fernet, InvalidToken

from vault import Vault


class PasswordManagerApp:
    def __init__(self, root: tk.Tk, fernet: Fernet, vault: Vault):
        self.root   = root
        self.fernet = fernet
        self.vault  = vault

        self.root.title("Gestionnaire de Mots de Passe")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        self._pending: dict[str, str] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        for label, builder in [
            ("  ➕  Ajouter / Modifier  ", self._build_add_tab),
            ("  🔍  Rechercher  ",         self._build_lookup_tab),
            ("  📋  Tous les sites  ",     self._build_list_tab),
        ]:
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=label)
            builder(frame)

        notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _build_add_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Nom du site :").grid(row=0, column=0, sticky="w", pady=6)
        self._add_site = ttk.Entry(parent, width=32)
        self._add_site.grid(row=0, column=1, padx=8, pady=6)
        self._add_site.bind("<Return>", lambda _: self._add_pw_entry.focus())

        ttk.Label(parent, text="Mot de passe :").grid(row=1, column=0, sticky="w", pady=6)
        self._add_pw_entry = ttk.Entry(parent, width=32, show="●")
        self._add_pw_entry.grid(row=1, column=1, padx=8, pady=6)
        self._add_pw_entry.bind("<Return>", lambda _: self._add_to_queue())

        self._show_add = tk.BooleanVar()
        ttk.Checkbutton(
            parent, text="Afficher", variable=self._show_add,
            command=lambda: self._add_pw_entry.config(show="" if self._show_add.get() else "●"),
        ).grid(row=1, column=2, padx=4)

        btn_row = ttk.Frame(parent)
        btn_row.grid(row=2, column=0, columnspan=3, pady=6)
        ttk.Button(btn_row, text="Ajouter à la liste",  command=self._add_to_queue).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="💾 Sauvegarder tout", command=self._save_all).pack(side=tk.LEFT, padx=4)

        ttk.Separator(parent, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Label(parent, text="En attente de sauvegarde :").grid(row=4, column=0, columnspan=3, sticky="w")

        q_frame = ttk.Frame(parent)
        q_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=4)
        sb = ttk.Scrollbar(q_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._queue_box = tk.Listbox(q_frame, height=6, yscrollcommand=sb.set)
        self._queue_box.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self._queue_box.yview)

    def _add_to_queue(self) -> None:
        site     = self._add_site.get().strip()
        password = self._add_pw_entry.get()
        if not site or not password:
            messagebox.showwarning("Champs vides", "Veuillez remplir le site et le mot de passe.", parent=self.root)
            return

        self._pending[site] = self.vault.encrypt_password(self.fernet, password)
        self._queue_box.delete(0, tk.END)
        for s in sorted(self._pending):
            self._queue_box.insert(tk.END, f"  {s}")

        self._add_site.delete(0, tk.END)
        self._add_pw_entry.delete(0, tk.END)
        self._add_site.focus()

    def _save_all(self) -> None:
        if not self._pending:
            messagebox.showinfo("Rien à sauvegarder", "Ajoutez d'abord des entrées.", parent=self.root)
            return
        self.vault.passwords.update(self._pending)
        self.vault.save()
        count = len(self._pending)
        self._pending.clear()
        self._queue_box.delete(0, tk.END)
        messagebox.showinfo("Succès", f"{count} entrée(s) sauvegardée(s).", parent=self.root)

    def _build_lookup_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Nom du site :").grid(row=0, column=0, sticky="w", pady=6)
        self._lookup_site = ttk.Entry(parent, width=32)
        self._lookup_site.grid(row=0, column=1, padx=8, pady=6)
        self._lookup_site.bind("<Return>", lambda _: self._lookup())
        ttk.Button(parent, text="Rechercher", command=self._lookup).grid(row=0, column=2, padx=4)

        ttk.Label(parent, text="Mot de passe :").grid(row=1, column=0, sticky="w", pady=6)
        self._result_var = tk.StringVar()
        self._result_entry = ttk.Entry(parent, textvariable=self._result_var, width=32, show="●", state="readonly")
        self._result_entry.grid(row=1, column=1, padx=8, pady=6)

        self._show_lookup = tk.BooleanVar()
        ttk.Checkbutton(
            parent, text="Afficher", variable=self._show_lookup,
            command=lambda: self._result_entry.config(show="" if self._show_lookup.get() else "●"),
        ).grid(row=1, column=2, padx=4)

        btn_row = ttk.Frame(parent)
        btn_row.grid(row=2, column=0, columnspan=3, pady=10)
        ttk.Button(btn_row, text="📋 Copier", command=self._copy).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Effacer",   command=self._clear_result).pack(side=tk.LEFT, padx=4)

        ttk.Separator(parent, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)
        self._status = ttk.Label(parent, text="", foreground="gray")
        self._status.grid(row=4, column=0, columnspan=3, sticky="w")

    def _lookup(self) -> None:
        site = self._lookup_site.get().strip()
        if not site:
            return
        if site not in self.vault.passwords:
            self._result_var.set("")
            self._status.config(text=f'Site introuvable : "{site}"', foreground="#c0392b")
            return
        try:
            self._result_var.set(self.vault.decrypt_password(self.fernet, site))
            self._status.config(text=f'Mot de passe trouvé pour "{site}".', foreground="#27ae60")
        except InvalidToken:
            messagebox.showerror("Erreur", "Impossible de déchiffrer cette entrée.", parent=self.root)

    def _copy(self) -> None:
        pw = self._result_var.get()
        if not pw:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(pw)
        self._status.config(text="Mot de passe copié dans le presse-papiers.", foreground="#2980b9")

    def _clear_result(self) -> None:
        self._result_var.set("")
        self._lookup_site.delete(0, tk.END)
        self._status.config(text="")

    def _build_list_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Sites enregistrés :").pack(anchor="w")

        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, pady=6)
        sb = ttk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._sites_box = tk.Listbox(frame, yscrollcommand=sb.set, height=10, activestyle="dotbox")
        self._sites_box.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self._sites_box.yview)

        btn_row = ttk.Frame(parent)
        btn_row.pack(pady=6)
        ttk.Button(btn_row, text="🔄 Rafraîchir", command=self._refresh_sites).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="🗑 Supprimer",  command=self._delete_site).pack(side=tk.LEFT, padx=4)

        self._refresh_sites()

    def _refresh_sites(self) -> None:
        self._sites_box.delete(0, tk.END)
        for site in sorted(self.vault.passwords):
            self._sites_box.insert(tk.END, f"  {site}")

    def _delete_site(self) -> None:
        sel = self._sites_box.curselection()
        if not sel:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un site à supprimer.", parent=self.root)
            return
        site = self._sites_box.get(sel[0]).strip()
        if messagebox.askyesno("Confirmer", f'Supprimer le mot de passe de "{site}" ?', parent=self.root):
            self.vault.remove(site)
            self.vault.save()
            self._refresh_sites()

    def _on_tab_change(self, event: tk.Event) -> None:
        if event.widget.index("current") == 2:
            self._refresh_sites()
