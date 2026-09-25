# -*- coding: utf-8 -*-
"""
Génère, à partir de palette.py :
  - lib/style_garmin_img/lines, polygons, points (style mkgmap)
  - garmin_img_typ_source.txt (source texte du TYP)
  - lib/garmin_img.typ (TYP compilé avec mkgmap, si java est disponible)

Usage (depuis le dossier du plugin ou n'importe où) :
    python scripts/generer_style_typ.py [chemin/vers/java]
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import palette as P  # noqa: E402

DOSSIER_STYLE = os.path.join(RACINE, "lib", "style_garmin_img")
SOURCE_TYP = os.path.join(RACINE, "garmin_img_typ_source.txt")
TYP_COMPILE = os.path.join(RACINE, "lib", "garmin_img.typ")
MKGMAP = os.path.join(RACINE, "lib", "mkgmap.jar")

FAMILY_ID = 6543
PRODUCT_ID = 1

# Niveau de zoom minimal d'affichage (24 = très rapproché seulement,
# 20 = visible aussi à des échelles plus larges)
RESOLUTION = 20

TAILLE_ICONE = P.TAILLE_ICONE

# Action mkgmap qui copie le tag name (champ d'étiquette choisi) dans
# l'étiquette Garmin. Sans elle, mkgmap n'affiche aucune étiquette.
ETIQUETTE = "{name '${name}'}"


def sans_accents(texte):
    # Les chaînes du TYP restent en ASCII pour éviter tout souci d'encodage
    return "".join(
        c for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )


def ecrire(chemin, lignes):
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")


# ----------------------------------------------------------------------
# Style mkgmap
# ----------------------------------------------------------------------

def generer_style():
    os.makedirs(DOSSIER_STYLE, exist_ok=True)
    entete = ["# Fichier généré par scripts/generer_style_typ.py - ne pas modifier à la main", ""]

    lignes = list(entete)
    for cle_c, _, _ in P.COULEURS:
        for cle_l, _, _ in P.LARGEURS:
            code = P.code_ligne(cle_c, cle_l)
            lignes.append(
                f"garmin_geom=ligne & garmin_couleur={cle_c} & garmin_largeur={cle_l} "
                f"{ETIQUETTE} [0x{code:02x} resolution {RESOLUTION}]"
            )
    ecrire(os.path.join(DOSSIER_STYLE, "lines"), lignes)

    polygones = list(entete)
    for cle_c, _, _ in P.COULEURS:
        code = P.code_polygone(cle_c)
        polygones.append(
            f"garmin_geom=polygone & garmin_couleur={cle_c} {ETIQUETTE} [0x{code:02x} resolution {RESOLUTION}]"
        )
    ecrire(os.path.join(DOSSIER_STYLE, "polygons"), polygones)

    points = list(entete)
    for cle_s, _, _, _ in P.symboles():
        code = P.code_point(cle_s)
        points.append(f"garmin_symbole={cle_s} {ETIQUETTE} [0x{code:04x} resolution {RESOLUTION}]")
    ecrire(os.path.join(DOSSIER_STYLE, "points"), points)

    ecrire(os.path.join(DOSSIER_STYLE, "info"), [
        "summary: Style du plugin garmin_img (palette de couleurs)",
        "version=2.0",
        "description {",
        "Style généré à partir de palette.py : une règle par couleur/largeur",
        "(lignes), par couleur (polygones) et par symbole (points).",
        "}",
    ])
    ecrire(os.path.join(DOSSIER_STYLE, "version"), ["1"])


# ----------------------------------------------------------------------
# TYP
# ----------------------------------------------------------------------

def generer_source_typ():
    l = [
        "; Fichier généré par scripts/generer_style_typ.py - ne pas modifier à la main",
        "[_id]",
        f"FID={FAMILY_ID}",
        f"ProductCode={PRODUCT_ID}",
        "CodePage=1252",
        "[end]",
        "",
        "[_drawOrder]",
    ]
    for cle_c, _, _ in P.COULEURS:
        l.append(f"Type=0x{P.code_polygone(cle_c):02x},1")
    l += ["[end]", ""]

    for cle_c, lib_c, hexa in P.COULEURS:
        for cle_l, lib_l, epaisseur in P.LARGEURS:
            l += [
                "[_line]",
                f"Type=0x{P.code_ligne(cle_c, cle_l):02x}",
                f"String={sans_accents(lib_c)} ({sans_accents(lib_l).lower()})",
                f"LineWidth={epaisseur}",
                'Xpm="0 0 1 0"',
                f'"a c {hexa}"',
                "[end]",
                "",
            ]

    for cle_c, lib_c, hexa in P.COULEURS:
        l += [
            "[_polygon]",
            f"Type=0x{P.code_polygone(cle_c):02x}",
            f"String={sans_accents(lib_c)}",
            'Xpm="0 0 1 0"',
            f'"a c {hexa}"',
            "[end]",
            "",
        ]

    for cle_s, lib_s, forme, cle_c in P.symboles():
        code = P.code_point(cle_s)
        remplissage = P.couleur_hex(cle_c)
        contour = "#FFFFFF" if cle_c == "noir" else "#000000"
        l += [
            "[_point]",
            f"Type=0x{code >> 8:02x}",
            f"SubType=0x{code & 0xff:02x}",
            f"String={sans_accents(lib_s)}",
            f'DayXpm="{TAILLE_ICONE} {TAILLE_ICONE} 3 1"',
            f'"a c {remplissage}"',
            f'"b c {contour}"',
            '". c none"',
        ]
        l += [f'"{rangee}"' for rangee in P.pixels_icone(forme, TAILLE_ICONE)]
        l += ["[end]", ""]

    ecrire(SOURCE_TYP, l)


def compiler_typ(java):
    dossier = tempfile.mkdtemp(prefix="typ_")
    try:
        source_tmp = os.path.join(dossier, "garmin_img.txt")
        shutil.copy(SOURCE_TYP, source_tmp)
        resultat = subprocess.run(
            [java, "-jar", MKGMAP, f"--family-id={FAMILY_ID}", f"--product-id={PRODUCT_ID}",
             f"--output-dir={dossier}", source_tmp],
            capture_output=True, text=True,
        )
        produit = os.path.join(dossier, "garmin_img.typ")
        if resultat.returncode != 0 or not os.path.isfile(produit):
            print(resultat.stdout)
            print(resultat.stderr)
            raise SystemExit("Échec de la compilation du TYP")
        shutil.copy(produit, TYP_COMPILE)
    finally:
        shutil.rmtree(dossier, ignore_errors=True)


if __name__ == "__main__":
    generer_style()
    generer_source_typ()
    print("Style et source TYP générés.")

    java = sys.argv[1] if len(sys.argv) > 1 else shutil.which("java")
    if java:
        compiler_typ(java)
        print(f"TYP compilé : {TYP_COMPILE}")
    else:
        print("java introuvable : le TYP n'a pas été compilé (passer le chemin de java en argument).")
