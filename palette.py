# -*- coding: utf-8 -*-
"""
Palette de couleurs et de symboles du plugin Garmin IMG.

Source unique de vérité : le dialogue s'en sert pour remplir les menus
déroulants, et scripts/generer_style_typ.py s'en sert pour générer le style
mkgmap (lib/style_garmin_img) et le TYP (lib/garmin_img.typ).

Après toute modification de ce fichier, relancer :
    python scripts/generer_style_typ.py
"""

# (clé interne, libellé affiché, couleur hexadécimale)
# La clé sert de valeur au tag garmin_couleur dans le .osm exporté :
# lettres minuscules, sans accent ni espace.
COULEURS = [
    ("rouge",       "Rouge",        "#E8210C"),
    ("orange",      "Orange",       "#FF8C00"),
    ("jaune",       "Jaune",        "#FFE000"),
    ("vert_lime",   "Vert lime",    "#9ACD00"),
    ("vert",        "Vert",         "#2E9A12"),
    ("vert_fonce",  "Vert foncé",   "#1E5A0E"),
    ("cyan",        "Cyan pâle",    "#B8F0FF"),
    ("bleu",        "Bleu",         "#0A8FD0"),
    ("bleu_marine", "Bleu marine",  "#0B3A6E"),
    ("violet",      "Violet",       "#8A2BE2"),
    ("rose",        "Rose",         "#FF66CC"),
    ("brun",        "Brun",         "#6B3A00"),
    ("noir",        "Noir",         "#000000"),
    ("gris_fonce",  "Gris foncé",   "#404040"),
    ("gris",        "Gris",         "#909090"),
    ("blanc",       "Blanc",        "#FFFFFF"),
]

# (clé interne, libellé affiché, épaisseur en pixels sur le GPS)
LARGEURS = [
    ("mince", "Mince", 1),
    ("moyen", "Moyen", 3),
    ("large", "Large", 5),
]

# Symboles de points : forme x couleur
FORMES = [
    ("rond",     "Rond"),
    ("carre",    "Carré"),
    ("diamant",  "Diamant"),
    ("triangle", "Triangle"),
]

COULEURS_POINTS = ["rouge", "orange", "jaune", "vert", "bleu", "violet", "noir", "blanc"]


def couleur_hex(cle):
    for c, _, h in COULEURS:
        if c == cle:
            return h
    raise KeyError(cle)


def libelle_couleur(cle):
    for c, lib, _ in COULEURS:
        if c == cle:
            return lib
    raise KeyError(cle)


def symboles():
    """Liste des symboles de points : (clé, libellé, forme, clé couleur)."""
    resultat = []
    for forme, lib_forme in FORMES:
        for couleur in COULEURS_POINTS:
            lib = f"{lib_forme} {libelle_couleur(couleur).lower()}"
            resultat.append((f"{forme}_{couleur}", lib, forme, couleur))
    return resultat


# ----------------------------------------------------------------------
# Icônes de points (même dessin dans le dialogue et sur le GPS)
# ----------------------------------------------------------------------

TAILLE_ICONE = 11


def masque_forme(forme, n=None):
    n = n or TAILLE_ICONE
    c = (n - 1) / 2
    masque = []
    for y in range(n):
        ligne = []
        for x in range(n):
            dx, dy = x - c, y - c
            if forme == "rond":
                dedans = dx * dx + dy * dy <= (c + 0.3) ** 2
            elif forme == "carre":
                dedans = abs(dx) <= c - 0.5 and abs(dy) <= c - 0.5
            elif forme == "diamant":
                dedans = abs(dx) + abs(dy) <= c + 0.3
            elif forme == "triangle":
                # pointe en haut, base en bas
                haut, bas = 0.5, n - 1.5
                if haut <= y <= bas:
                    demi = (y - haut) / (bas - haut) * c + 0.4
                    dedans = abs(dx) <= demi
                else:
                    dedans = False
            else:
                raise ValueError(forme)
            ligne.append(dedans)
        masque.append(ligne)
    return masque


def pixels_icone(forme, n=None):
    """Retourne les lignes XPM : 'a' = remplissage, 'b' = contour, '.' = transparent."""
    n = n or TAILLE_ICONE
    m = masque_forme(forme, n)

    def dedans(x, y):
        return 0 <= x < n and 0 <= y < n and m[y][x]

    lignes = []
    for y in range(n):
        s = ""
        for x in range(n):
            if not m[y][x]:
                s += "."
            elif all(dedans(x + ox, y + oy) for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                s += "a"
            else:
                s += "b"
        lignes.append(s)
    return lignes


# ----------------------------------------------------------------------
# Codes Type Garmin (codes classiques uniquement)
# ----------------------------------------------------------------------

# Lignes : 0x01-0x3f, sauf 0x20-0x25 (courbes de niveau : certains GPS leur
# appliquent un traitement spécial, ex. étiquettes converties en altitude).
CODES_LIGNES = [c for c in range(0x01, 0x40) if not 0x20 <= c <= 0x25]

# Polygones : 0x01-0x7f, sauf 0x4a (zone de définition) et 0x4b (fond de
# carte), réservés par le format Garmin.
CODES_POLYGONES = [c for c in range(0x01, 0x80) if c not in (0x4a, 0x4b)]

# Points : type 0x64 avec sous-types 0x00-0x1f (32 symboles maximum)
CODE_POINT_BASE = 0x6400


def code_ligne(cle_couleur, cle_largeur):
    i_c = [c for c, _, _ in COULEURS].index(cle_couleur)
    i_l = [l for l, _, _ in LARGEURS].index(cle_largeur)
    return CODES_LIGNES[i_c * len(LARGEURS) + i_l]


def code_polygone(cle_couleur):
    i_c = [c for c, _, _ in COULEURS].index(cle_couleur)
    return CODES_POLYGONES[i_c]


def code_point(cle_symbole):
    i_s = [s[0] for s in symboles()].index(cle_symbole)
    return CODE_POINT_BASE + i_s


assert len(COULEURS) * len(LARGEURS) <= len(CODES_LIGNES), "Trop de couleurs x largeurs pour les codes de lignes"
assert len(COULEURS) <= len(CODES_POLYGONES)
assert len(FORMES) * len(COULEURS_POINTS) <= 32, "Maximum 32 symboles de points"
