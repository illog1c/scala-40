# logic.py – Parsing e generazione combinazioni valide dalla mano

from itertools import combinations, groupby
from collections import defaultdict
from src.core import SEMI, VALORI, JOLLY

def parse_mano(mano):
    """
    Accetta la mano come lista di tuple (valore, seme).
    Restituisce dizionario con:
    - carte_per_seme: dict seme -> lista valori
    - carte_per_valore: dict valore -> lista semi
    - jolly: lista di jolly presenti
    """
    carte_per_seme = defaultdict(list)
    carte_per_valore = defaultdict(list)
    jolly = []

    for valore, seme in mano:
        if valore == "JOLLY":
            jolly.append((valore, seme))
        else:
            carte_per_seme[seme].append(valore)
            carte_per_valore[valore].append(seme)

    # Ordina le carte nei semi per ordine nominale
    for seme in carte_per_seme:
        carte_per_seme[seme].sort(key=lambda v: VALORI.index(v))

    return {
        "per_seme": dict(carte_per_seme),
        "per_valore": dict(carte_per_valore),
        "jolly": jolly
    }

def genera_combinazioni(mano):
    """
    Genera tutte le combinazioni valide (scale, tris, poker), con e senza jolly.
    Restituisce una lista di dict:
        {
            'tipo': 'tris' | 'scala',
            'carte': [(valore, seme), ...],
            'punti': int
        }
    """
    parsed = parse_mano(mano)
    combinazioni = []

    # === TRIS e POKER ===
    for valore, semi in parsed["per_valore"].items():
        if len(semi) >= 3:
            tris = [(valore, s) for s in semi[:3]]
            combinazioni.append({
                "tipo": "tris",
                "carte": tris,
                "punti": calcola_punti_combinazione(tris)
            })
        if len(semi) == 4:
            poker = [(valore, s) for s in semi]
            combinazioni.append({
                "tipo": "tris",
                "carte": poker,
                "punti": calcola_punti_combinazione(poker)
            })
        elif len(semi) == 2 and parsed["jolly"]:
            tris = [(valore, s) for s in semi] + [parsed["jolly"][0]]
            combinazioni.append({
                "tipo": "tris",
                "carte": tris,
                "punti": calcola_punti_combinazione(tris)
            })

    # === SCALE ===
    for seme, valori in parsed["per_seme"].items():
        indici = [VALORI.index(v) for v in valori]
        indici = sorted(set(indici))
        sequenze = estrai_sequenze_consecutive(indici)

        for seq in sequenze:
            if len(seq) >= 3:
                carte = [(VALORI[i], seme) for i in seq]
                combinazioni.append({
                    "tipo": "scala",
                    "carte": carte,
                    "punti": calcola_punti_combinazione(carte)
                })
            # con jolly (max uno)
            elif len(seq) == 2 and parsed["jolly"]:
                carte = [(VALORI[i], seme) for i in seq] + [parsed["jolly"][0]]
                combinazioni.append({
                    "tipo": "scala",
                    "carte": carte,
                    "punti": calcola_punti_combinazione(carte)
                })

    return combinazioni

def estrai_sequenze_consecutive(indici):
    """
    Riceve lista ordinata di indici numerici (es. [4,5,6,9])
    Restituisce lista di liste con sequenze consecutive
    """
    sequenze = []
    for k, g in groupby(enumerate(indici), lambda x: x[1] - x[0]):
        gruppo = list(map(lambda x: x[1], g))
        sequenze.append(gruppo)
    return sequenze

def calcola_punti_combinazione(combinazione):
    """
    Calcola i punti totali per una scala o tris (con jolly)
    """
    punti = 0
    for valore, seme in combinazione:
        if valore == "JOLLY":
            continue
        if valore == "A":
            punti += 11
        elif valore in ["J", "Q", "K"]:
            punti += 10
        else:
            punti += int(valore)
    return punti


from itertools import combinations as combo_set

def scegli_apertura(combinazioni, mano):
    """
    Sceglie il miglior insieme di combinazioni disgiunte per aprire con almeno 40 punti.
    Preferisce combinazioni che:
        - non usano carte in comune
        - totalizzano >= 40 punti
        - usano meno combinazioni possibili
        - usano meno jolly possibili
        - massimizzano il punteggio (in caso di parità)
    """
    migliori = []
    max_punti = 0

    # Genera tutte le combinazioni di gruppi di combinazioni
    for r in range(1, len(combinazioni)+1):
        for gruppo in combo_set(combinazioni, r):
            carte_usate = []
            jolly_usati = 0
            punti = 0
            valido = True

            for c in gruppo:
                for carta in c["carte"]:
                    if carta in carte_usate:
                        valido = False
                        break
                    if carta[0] == "JOLLY":
                        jolly_usati += 1
                        if jolly_usati > len([c for c in mano if c[0] == "JOLLY"]):
                            valido = False
                            break
                    carte_usate.append(carta)
                if not valido:
                    break
                punti += c["punti"]

            if valido and punti >= 40:
                if (
                    not migliori or
                    punti > max_punti or
                    (punti == max_punti and len(gruppo) < len(migliori))
                ):
                    migliori = gruppo
                    max_punti = punti

    if not migliori:
        return {
            "puo_aprire": False,
            "combinazioni": [],
            "punti": 0,
            "carte_rimaste": mano
        }

    # Calcola le carte rimaste in mano dopo l'apertura
    carte_apertura = set()
    for c in migliori:
        for carta in c["carte"]:
            carte_apertura.add(carta)

    carte_rimaste = [c for c in mano if c not in carte_apertura]

    return {
        "puo_aprire": True,
        "combinazioni": list(migliori),
        "punti": max_punti,
        "carte_rimaste": carte_rimaste
    }


def suggerisci_scarto(carte_rimaste, combinazioni_possibili=None):
    """
    Suggerisce la miglior carta da scartare:
    - non jolly
    - non utile per future scale/tris
    - minimizza punti
    - evita di lasciare carte potenzialmente utili all'avversario
    """
    if not carte_rimaste:
        return None

    # Non scartare jolly
    carte = [c for c in carte_rimaste if c[0] != "JOLLY"]
    if not carte:
        return None  # solo jolly rimasti

    # Costruisci dizionari d'appoggio
    per_seme = defaultdict(list)
    per_valore = defaultdict(list)
    for valore, seme in carte:
        per_seme[seme].append(valore)
        per_valore[valore].append(seme)

    rischi = {}
    for carta in carte:
        valore, seme = carta
        score = 0

        idx = VALORI.index(valore)

        # Punteggio nominale (più alto = peggio tenerla)
        if valore == "A":
            score += 11
        elif valore in ["J", "Q", "K"]:
            score += 10
        else:
            score += int(valore)

        # Penalità se la carta è "in mezzo" a una possibile scala (es: 5 con 4 e 6 presenti)
        vicini = []
        if idx > 0:
            vicini.append(VALORI[idx - 1])
        if idx < len(VALORI) - 1:
            vicini.append(VALORI[idx + 1])

        vicini_presenti = sum(1 for v in vicini if v in per_seme[seme])
        score -= 5 * vicini_presenti  # più vicini = più utile = meno desiderabile scartarla

        # Bonus se è una carta "solitaria" (non aiuta in nulla)
        if len(per_valore[valore]) == 1 and len(per_seme[seme]) == 1:
            score -= 3

        rischi[carta] = score

    # Ordina per punteggio crescente
    migliori = sorted(rischi.items(), key=lambda x: x[1])
    return migliori[0][0]  # carta con punteggio più basso


def suggerisci_scarto(carte_rimaste, combinazioni_possibili=None):
    """
    Suggerisce lo scarto ottimale valutando:
    - punti nominali (più alti = più pericolosi)
    - rischio di completamento scala (propria o avversaria)
    - utilità nei tris
    - isolamento (nessuna carta vicina o stesso valore)
    - valore strategico (carte centrali più flessibili)
    - evita jolly
    """
    if not carte_rimaste:
        return None

    carte = [c for c in carte_rimaste if c[0] != "JOLLY"]
    if not carte:
        return None  # solo jolly rimasti

    score_map = {}
    per_seme = defaultdict(list)
    per_valore = defaultdict(list)

    for valore, seme in carte:
        per_seme[seme].append(valore)
        per_valore[valore].append(seme)

    for carta in carte:
        valore, seme = carta
        idx = VALORI.index(valore)
        score = 0

        # === BASE: punti carta ===
        if valore == "A":
            score += 11
        elif valore in ["J", "Q", "K"]:
            score += 10
        else:
            score += int(valore)

        # === BONUS negativo (cioè penalità per l'eliminazione) ===
        # ➤ potenziale scala
        vicini = []
        if idx > 0:
            vicini.append(VALORI[idx - 1])
        if idx < len(VALORI) - 1:
            vicini.append(VALORI[idx + 1])

        vicini_presenti = sum(1 for v in vicini if v in per_seme[seme])
        score -= 7 * vicini_presenti  # forte penalità se vicini presenti

        # ➤ valore centrale in possibili scale (es. 6, 7, 8)
        if 2 < idx < 11:
            score -= 2

        # ➤ parte di coppia o tris potenziale
        if len(per_valore[valore]) > 1:
            score -= 4 * (len(per_valore[valore]) - 1)

        # ➤ carta isolata (nessun altro stesso valore o seme vicino)
        if len(per_valore[valore]) == 1 and vicini_presenti == 0:
            score += 2  # è sacrificabile

        # === PROTEZIONE strategica ===
        # Penalizza se è l'unico valore basso in una scala che ha già 2 elementi
        if valore in VALORI[1:-1]:
            idx_v = VALORI.index(valore)
            if (
                idx_v > 1 and VALORI[idx_v - 2] in per_seme[seme] and VALORI[idx_v - 1] in per_seme[seme]
            ) or (
                idx_v < len(VALORI) - 2 and VALORI[idx_v + 1] in per_seme[seme] and VALORI[idx_v + 2] in per_seme[seme]
            ):
                score -= 5

        score_map[carta] = score

    ordinata = sorted(score_map.items(), key=lambda x: x[1])
    return ordinata[0][0]


def suggerisci_scarto(carte_rimaste, combinazioni_possibili=None):
    """
    Suggerisce sempre una carta da scartare, anche nei casi estremi.
    Basato su logica strategica e statistica.
    """
    if not carte_rimaste:
        return None

    # Evita jolly: li tiene fuori dalla valutazione
    carte = [c for c in carte_rimaste if c[0] != "JOLLY"]
    if not carte:
        carte = carte_rimaste[:]  # Se ho solo jolly, li valuto comunque (caso limite)

    score_map = {}
    per_seme = defaultdict(list)
    per_valore = defaultdict(list)

    for valore, seme in carte:
        per_seme[seme].append(valore)
        per_valore[valore].append(seme)

    for carta in carte:
        valore, seme = carta
        idx = VALORI.index(valore)
        score = 0

        # Punti nominali
        if valore == "A":
            score += 11
        elif valore in ["J", "Q", "K"]:
            score += 10
        else:
            score += int(valore)

        # Rischio scala
        vicini = []
        if idx > 0:
            vicini.append(VALORI[idx - 1])
        if idx < len(VALORI) - 1:
            vicini.append(VALORI[idx + 1])
        vicini_presenti = sum(1 for v in vicini if v in per_seme[seme])
        score -= 7 * vicini_presenti

        # Valori centrali
        if 2 < idx < 11:
            score -= 2

        # Parte di tris
        if len(per_valore[valore]) > 1:
            score -= 4 * (len(per_valore[valore]) - 1)

        # Carta isolata
        if len(per_valore[valore]) == 1 and vicini_presenti == 0:
            score += 2

        # Scala lunga potenziale
        if valore in VALORI[1:-1]:
            idx_v = VALORI.index(valore)
            if (
                idx_v > 1 and VALORI[idx_v - 2] in per_seme[seme] and VALORI[idx_v - 1] in per_seme[seme]
            ) or (
                idx_v < len(VALORI) - 2 and VALORI[idx_v + 1] in per_seme[seme] and VALORI[idx_v + 2] in per_seme[seme]
            ):
                score -= 5

        score_map[carta] = score

    ordinata = sorted(score_map.items(), key=lambda x: x[1])
    return ordinata[0][0]  # Sempre una carta
