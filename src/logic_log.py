
from collections import defaultdict, Counter

VALORI = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def suggerisci_scarto(carte_rimaste, combinazioni_possibili=None, carte_giocate=None):
    if not carte_rimaste:
        return None, ["⚠️ Nessuna carta in mano"]

    log = []
    carte = [c for c in carte_rimaste if c[0] != "JOLLY"]
    if not carte:
        carte = carte_rimaste[:]

    score_map = {}
    per_seme = defaultdict(list)
    per_valore = defaultdict(list)

    # Costruzione strutture basate SOLO sulle carte rimaste
    for valore, seme in carte:
        if valore in VALORI:
            per_seme[seme].append(valore)
            per_valore[valore].append(seme)

    # Analisi carte già giocate (per stimare probabilità)
    conteggio_giocate = Counter()
    if carte_giocate:
        for v, s in carte_giocate:
            conteggio_giocate[v] += 1

    for carta in carte:
        valore, seme = carta
        score = 0
        riga_log = [f"🔍 Valutazione {valore}{seme}:"]
        
        if valore not in VALORI:
            riga_log.append("  - È un jolly (scarto mai consigliato)")
            score += 100
            score_map[carta] = score
            log.append("\n".join(riga_log))
            continue

        idx = VALORI.index(valore)

        # Valore base da regolamento
        valore_punti = {"A": 11, "J": 10, "Q": 10, "K": 10}
        if valore in valore_punti:
            base = valore_punti[valore]
        else:
            try:
                base = int(valore)
            except ValueError:
                base = 0
        score += base
        riga_log.append(f"  - Valore in mano secondo regolamento (+{base})")

        # Vicini di scala
        vicini = []
        if idx > 0:
            vicini.append(VALORI[idx - 1])
        if idx < len(VALORI) - 1:
            vicini.append(VALORI[idx + 1])
        vicini_presenti = sum(1 for v in vicini if v in per_seme[seme])
        if vicini_presenti:
            penalty = 7 * vicini_presenti
            score -= penalty
            riga_log.append(f"  - Vicini nella scala trovati: {vicini_presenti} (–{penalty})")
        else:
            riga_log.append("  - Nessun vicino di scala")

        # Potenziale attacco con jolly
        if valore in ["2", "4"] and "3" not in per_seme[seme]:
            score -= 5
            riga_log.append("  - Potenziale attacco con JOLLY o 3 (–5)")

        # Bonus valore intermedio
        if 2 < idx < 11:
            score -= 2
            riga_log.append("  - Valore intermedio (–2)")

        # Possibile tris
        if len(per_valore[valore]) > 1:
            bonus = 4 * (len(per_valore[valore]) - 1)
            score -= bonus
            riga_log.append(f"  - Possibile tris con altri {len(per_valore[valore]) - 1} (–{bonus})")

        # Penalità se carta già giocata
        num_giocate = conteggio_giocate[valore]
        if num_giocate > 0:
            penalita = num_giocate * 3
            score += penalita
            riga_log.append(f"  - {num_giocate} carta/e già giocate con questo valore (+{penalita})")

        # Penalità se isolata
        if len(per_valore[valore]) == 1 and vicini_presenti == 0:
            if valore in ["10", "J", "Q", "K", "A"]:
                score += 4
                riga_log.append("  - Carta isolata alta (+4)")
            else:
                score += 1
                riga_log.append("  - Carta isolata (+1)")

        riga_log.append(f"  => Punteggio finale: {score}")
        log.append("\n".join(riga_log))
        score_map[carta] = score

    scarto = max(score_map.items(), key=lambda x: x[1])[0]
    log.insert(0, f"🗑️ Carta consigliata da scartare: {scarto[0]}{scarto[1]}")
    return scarto, log
