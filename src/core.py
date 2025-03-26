# core.py

SEMI = ["♥", "♦", "♣", "♠"]
VALORI = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def tutte_le_carte():
    carte = []
    for seme in SEMI:
        for valore in VALORI:
            carte.append((valore, seme))
    return carte

# Jolly rappresentato come valore "JOLLY" e seme None
JOLLY = ("JOLLY", None)