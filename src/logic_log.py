from collections import defaultdict, Counter

VALORI = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

FASE_PESI = {
    "inizio": {"valore": 0.5, "strategia": 1.2, "rischio": 1.0},
    "centrale": {"valore": 1.0, "strategia": 1.0, "rischio": 1.0},
    "finale": {"valore": 1.5, "strategia": 0.8, "rischio": 1.2},
}

def suggerisci_scarto(carte_rimaste, combinazioni_possibili=None, carte_giocate=None, fase="centrale"):
    if not carte_rimaste:
        return None, ["⚠️ Nessuna carta in mano"]

    log = []
    carte = [c for c in carte_rimaste if c[0] != "JOLLY"]
    if not carte:
        carte = carte_rimaste[:]

    score_map = {}
    per_seme = defaultdict(list)
    per_valore = defaultdict(list)

    for valore, seme in carte:
        if valore in VALORI:
            per_seme[seme].append(valore)
            per_valore[valore].append(seme)

    conteggio_giocate = Counter()
    if carte_giocate:
        for v, s in carte_giocate:
            conteggio_giocate[v] += 1

    pesi = FASE_PESI.get(fase, FASE_PESI["centrale"])

    for carta in carte:
        valore, seme = carta
        score = 0
        riga_log = [f"🔍 Valutazione {valore}{seme} (fase: {fase}):"]

        if valore not in VALORI:
            riga_log.append("  - È un jolly (scarto mai consigliato)")
            score += 100
            score_map[carta] = score
            log.append("\n".join(riga_log))
            continue

        idx = VALORI.index(valore)

        valore_punti = {"A": 11, "J": 10, "Q": 10, "K": 10}
        base = valore_punti.get(valore, 10 if valore in ["J", "Q", "K"] else int(valore))
        score += base * pesi["valore"]
        riga_log.append(f"  - Valore in mano secondo regolamento (+{base}×{pesi['valore']}={base * pesi['valore']})")

        if pesi["valore"] < 1 and base >= 10:
            penalita_alta = 5
            score += penalita_alta
            riga_log.append(f"  - Penalità carta alta iniziale (+{penalita_alta})")

        vicini = []
        if idx > 0:
            vicini.append(VALORI[idx - 1])
        if idx < len(VALORI) - 1:
            vicini.append(VALORI[idx + 1])
        vicini_presenti = sum(1 for v in vicini if v in per_seme[seme])
        bonus_scala = 7 * vicini_presenti * pesi["strategia"]
        if vicini_presenti:
            score -= bonus_scala
            riga_log.append(f"  - Vicini nella scala trovati: {vicini_presenti} (–{bonus_scala})")
        else:
            riga_log.append("  - Nessun vicino di scala")

        if valore in ["2", "4"] and "3" not in per_seme[seme]:
            potenziale_attacco = 5 * pesi["strategia"]
            score -= potenziale_attacco
            riga_log.append(f"  - Potenziale attacco con JOLLY o 3 (–{potenziale_attacco})")

        if 2 < idx < 11:
            bonus_intermedio = 2 * pesi["strategia"]
            score -= bonus_intermedio
            riga_log.append(f"  - Valore intermedio (–{bonus_intermedio})")

        if len(per_valore[valore]) > 1:
            bonus_tris = 4 * (len(per_valore[valore]) - 1) * pesi["strategia"]
            score -= bonus_tris
            riga_log.append(f"  - Possibile tris con altri {len(per_valore[valore]) - 1} (–{bonus_tris})")

        num_giocate = conteggio_giocate[valore]
        penalita_giocate = num_giocate * 3 * pesi["rischio"]
        if num_giocate > 0:
            score += penalita_giocate
            riga_log.append(f"  - {num_giocate} carta/e già giocate con questo valore (+{penalita_giocate})")

        if len(per_valore[valore]) == 1 and vicini_presenti == 0:
            penalita_isolata = 4 if valore in ["10", "J", "Q", "K", "A"] else 1
            score += penalita_isolata
            riga_log.append(f"  - Carta isolata (+{penalita_isolata})")

        riga_log.append(f"  => Punteggio finale: {score:.1f}")
        log.append("\n".join(riga_log))
        score_map[carta] = score

    scarto = max(score_map.items(), key=lambda x: x[1])[0]
    log.insert(0, f"🗑️ Carta consigliata da scartare: {scarto[0]}{scarto[1]}")
    return scarto, log
