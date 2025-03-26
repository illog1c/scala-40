# gui.py – Aggiunge suggerimenti apertura e scarto in sezione fissa

import tkinter as tk
from tkinter import messagebox
from src.core import SEMI, VALORI
from src.logic import genera_combinazioni, scegli_apertura, suggerisci_scarto
from src.logic_log import suggerisci_scarto

from collections import defaultdict

MAX_CARTE = 13
CARD_WIDTH = 60
CARD_HEIGHT = 85

COLOR_BG = "#1e1e1e"
COLOR_FRAME = "#2e2e2e"
COLOR_TEXT = "#ffffff"
COLOR_BTN = "#007acc"
COLOR_CARD_BG = "#f2f2f2"
COLOR_ROW_UNIFORM = "#2a2a2a"

SEMI_ALTERNATI = [("♥", "red"), ("♣", "black"), ("♦", "red"), ("♠", "black")]

class CartaGUI(tk.Canvas):
    def __init__(self, master, valore, seme, drag_callback=None):
        super().__init__(master, width=CARD_WIDTH, height=CARD_HEIGHT, bg=COLOR_CARD_BG,
                         highlightthickness=1, highlightbackground="#ccc")
        self.valore = valore
        self.seme = seme
        self.drag_callback = drag_callback
        self.bind("<Button-1>", self.on_click)

        if valore == "JOLLY":
            colore = "red" if "red" in seme else "black"
            self.create_text(CARD_WIDTH // 2, CARD_HEIGHT // 2, text="★ JOLLY",
                             font=("Segoe UI", 10, "bold"), fill=colore, anchor="center")
        else:
            colore = "red" if seme in ["♥", "♦"] else "black"
            self.create_text(8, 10, text=valore, anchor="nw",
                             font=("Segoe UI", 12, "bold"), fill=colore)
            self.create_text(CARD_WIDTH - 8, CARD_HEIGHT - 10, text=seme,
                             anchor="se", font=("Segoe UI", 16), fill=colore)

    def on_click(self, event):
        if self.drag_callback:
            self.drag_callback((self.valore, self.seme), self)

def tutte_le_carte_ordinate_con_jolly():
    righe = []
    for seme, colore in SEMI_ALTERNATI:
        carte = [(valore, seme) for valore in VALORI]
        righe.append((carte, colore, seme))
    return righe

def avvia_gui():
    root = tk.Tk()
    root.title("Scala 40 – Seleziona la tua mano")
    root.geometry("1200x900")
    root.configure(bg=COLOR_BG)

    frame_disponibili = tk.LabelFrame(root, text="Carte disponibili", bg=COLOR_FRAME, fg=COLOR_TEXT,
                                      font=("Segoe UI", 11, "bold"))
    frame_disponibili.pack(padx=20, pady=10, fill="both", expand=True)

    frame_mano = tk.LabelFrame(root, text="La tua mano", bg=COLOR_FRAME, fg=COLOR_TEXT,
                               font=("Segoe UI", 11, "bold"))
    frame_mano.pack(padx=20, pady=10, fill="x")

    frame_info = tk.LabelFrame(root, text="Suggerimenti dell'algoritmo", bg=COLOR_FRAME, fg=COLOR_TEXT,
                                font=("Segoe UI", 11, "bold"))
    frame_info.pack(padx=20, pady=5, fill="both")

    text_info = tk.Text(frame_info, height=10, bg=COLOR_BG, fg=COLOR_TEXT, font=("Segoe UI", 10), wrap="word")
    text_info.pack(fill="both", padx=5, pady=5)
    text_info.config(state="disabled")

    righe_info = tutte_le_carte_ordinate_con_jolly()
    mano = []
    carte_gui_map = {}
    righe_frame = []
    righe_carte = []

    def aggiorna_info(msg):
        text_info.config(state="normal")
        text_info.delete("1.0", tk.END)
        text_info.insert(tk.END, msg)
        text_info.config(state="disabled")

    def aggiungi_a_mano(carta, widget_gui):
        if carta in mano:
            return
        if len(mano) >= MAX_CARTE:
            messagebox.showwarning("Limite raggiunto", f"Puoi selezionare al massimo {MAX_CARTE} carte.")
            return
        mano.append(carta)
        righe_carte_rimuovi(carta)
        ridisegna_mano()
        rigenera_righe()

    def rimuovi_da_mano(carta, widget_gui):
        if carta in mano:
            mano.remove(carta)
            righe_carte_aggiungi(carta)
            ridisegna_mano()
            rigenera_righe()

    def righe_carte_rimuovi(carta):
        for riga in righe_carte:
            if carta in riga:
                riga.remove(carta)

    def righe_carte_aggiungi(carta):
        valore, seme = carta
        if valore == "JOLLY":
            riga_index = int(seme.split("-")[0][1])
            righe_carte[riga_index].append(carta)
        else:
            for idx, (_, _, seme_riga) in enumerate(righe_info):
                if seme == seme_riga:
                    righe_carte[idx].append(carta)

    def rigenera_righe():
        for idx, frame in enumerate(righe_frame):
            for widget in frame.winfo_children():
                widget.destroy()
            carte_ordinate = sorted(righe_carte[idx], key=lambda c: (99 if c[0] == "JOLLY" else VALORI.index(c[0])))
            for valore, seme in carte_ordinate:
                carta = CartaGUI(frame, valore, seme, aggiungi_a_mano)
                carta.pack(side=tk.LEFT, padx=3, pady=3)
                carte_gui_map[(valore, seme)] = carta

    def ridisegna_mano():
        for widget in frame_mano.winfo_children():
            widget.destroy()
        for valore, seme in mano:
            carta = CartaGUI(frame_mano, valore, seme, lambda c, w=None, v=valore, s=seme: rimuovi_da_mano((v, s), None))
            carta.pack(side=tk.LEFT, padx=5, pady=5)

    
    def suggerisci():
        if len(mano) != MAX_CARTE:
            messagebox.showerror("Errore", "Devi selezionare esattamente 13 carte.")
            return

        combinazioni = genera_combinazioni(mano)
        apertura = scegli_apertura(combinazioni, mano)
        msg = ""

        if not apertura["puo_aprire"]:
            msg += "Non è possibile aprire con la mano attuale."

        else:
            msg += f"✅ Apertura consigliata ({apertura['punti']} punti):"

            for c in apertura["combinazioni"]:
                tipo = "Scala" if c["tipo"] == "scala" else "Tris"
                descrizione = ", ".join([f"{v}{s}" if v != "JOLLY" else "★" for v, s in c["carte"]])
                msg += f" - {tipo}: {descrizione}"


        scarto, log = suggerisci_scarto(apertura["carte_rimaste"])
        msg += f"\n🗑️ Scarto consigliato: {scarto[0]}{scarto[1]}\n\n"
        msg += "\n".join(log)
        aggiorna_info(msg)


    for riga_index, (carte, colore, seme_riga) in enumerate(righe_info):
        frame_riga = tk.Frame(frame_disponibili, bg=COLOR_ROW_UNIFORM)
        frame_riga.pack(pady=2, fill="x")
        righe_frame.append(frame_riga)

        lista_carte = carte[:]
        seme_fittizio = f"J{riga_index}-{colore}"
        lista_carte.append(("JOLLY", seme_fittizio))
        righe_carte.append(lista_carte)

    rigenera_righe()

    btn_frame = tk.Frame(root, bg=COLOR_BG)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Suggerisci apertura e scarto", command=suggerisci,
              font=("Segoe UI", 11, "bold"), bg=COLOR_BTN, fg="white",
              relief="flat", padx=10, pady=5).pack()

    root.mainloop()