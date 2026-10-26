"""Calcul des objectifs nutritionnels journaliers (Sprint 1).

Entrées  : âge, sexe, taille, poids, niveau d'activité, objectif.
Sorties  : kcal, protéines, glucides, lipides par jour (+ détails et avertissements).

Chaîne de calcul
    BMR      = Mifflin-St Jeor
    TDEE     = BMR x facteur d'activité
    kcal     = TDEE ajusté selon l'objectif (déficit plafonné, plancher = BMR)
    protéines= g/kg x poids, plafonnées à 35 % de l'énergie
    lipides  = 25 % des kcal
    glucides = le reste, avec contrôle de la plage AMDR (45 à 65 %)

Les estimations sont indicatives et ne remplacent pas un avis médical.
"""

import math

# --------------------------------------------------------------------------
# Paramètres (un seul endroit à modifier)
# --------------------------------------------------------------------------
FACTEURS_ACTIVITE = {
    "sedentaire": 1.2,
    "leger": 1.375,
    "modere": 1.55,
    "actif": 1.725,
}

OBJECTIFS = ("perte", "maintien", "prise")

DEFICIT_PERTE = 0.20          # 20 % de la dépense totale
DEFICIT_MAX_KCAL = 500        # plafond du déficit (environ 0,45 kg/semaine)
SURPLUS_PRISE = 0.10          # +10 % de la dépense totale

PROT_G_PAR_KG_PERTE = 1.8
PROT_G_PAR_KG_AUTRE = 1.6
PROT_G_PAR_KG_MIN = 1.4       # borne basse (plage ISSN 1,4 à 2,0 g/kg)
LIPIDES_PART = 0.25           # 25 % des kcal
LIPIDES_PART_MIN = 0.20       # bornes AMDR : lipides 20 à 35 %
LIPIDES_PART_MAX = 0.35

# Plages AMDR (part de l'énergie)
GLUCIDES_PART_MIN = 0.45
GLUCIDES_PART_MAX = 0.65
PROT_PART_MIN = 0.10
PROT_PART_MAX = 0.35

IMC_MIN_POUR_PERTE = 18.5     # pas d'objectif de perte en insuffisance pondérale

# Seuils d'avertissement : valeurs courantes, A CONFIRMER sur une source officielle
SEUIL_KCAL_BAS = {"F": 1200, "H": 1500}

AGE_MIN, AGE_MAX = 18, 100    # adultes uniquement
TAILLE_MIN, TAILLE_MAX = 120, 230
POIDS_MIN, POIDS_MAX = 30, 300

KCAL_PAR_G = {"prot": 4, "gluc": 4, "lip": 9}


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------
def _arrondi(x):
    """Arrondi classique (0,5 vers le haut), contrairement à round() de Python."""
    return int(math.floor(x + 0.5))


def _verifier_nombre(nom, valeur, minimum, maximum):
    if isinstance(valeur, bool) or not isinstance(valeur, (int, float)):
        raise ValueError(f"{nom} doit être un nombre.")
    if not (minimum <= valeur <= maximum):
        raise ValueError(f"{nom} doit être compris entre {minimum} et {maximum}.")


def valider_entrees(age, sexe, taille_cm, poids_kg, activite, objectif):
    """Lève ValueError avec un message clair si une entrée est invalide."""
    _verifier_nombre("L'âge", age, AGE_MIN, AGE_MAX)
    if sexe not in ("H", "F"):
        raise ValueError("Le sexe doit être 'H' ou 'F'.")
    _verifier_nombre("La taille (cm)", taille_cm, TAILLE_MIN, TAILLE_MAX)
    _verifier_nombre("Le poids (kg)", poids_kg, POIDS_MIN, POIDS_MAX)
    if activite not in FACTEURS_ACTIVITE:
        raise ValueError(
            f"Niveau d'activité inconnu : choisir parmi {sorted(FACTEURS_ACTIVITE)}."
        )
    if objectif not in OBJECTIFS:
        raise ValueError(f"Objectif inconnu : choisir parmi {list(OBJECTIFS)}.")

    imc = poids_kg / (taille_cm / 100) ** 2
    if objectif == "perte" and imc < IMC_MIN_POUR_PERTE:
        raise ValueError(
            f"Objectif de perte refusé : IMC de {imc:.1f}, inférieur à {IMC_MIN_POUR_PERTE}."
        )


# --------------------------------------------------------------------------
# Étapes du calcul
# --------------------------------------------------------------------------
def metabolisme_base(age, sexe, taille_cm, poids_kg):
    """Équation de Mifflin-St Jeor (kcal/jour)."""
    base = 10 * poids_kg + 6.25 * taille_cm - 5 * age
    return base + 5 if sexe == "H" else base - 161


def objectif_calorique(tdee, bmr, objectif):
    """Applique l'ajustement selon l'objectif. Retourne (kcal, avertissements)."""
    avertissements = []
    if objectif == "perte":
        deficit = min(DEFICIT_PERTE * tdee, DEFICIT_MAX_KCAL)
        kcal = tdee - deficit
        if kcal < bmr:                      # plancher de sécurité
            kcal = bmr
            avertissements.append(
                "Objectif relevé au niveau du métabolisme de base (plancher de sécurité)."
            )
    elif objectif == "prise":
        kcal = tdee * (1 + SURPLUS_PRISE)
    else:
        kcal = tdee
    return kcal, avertissements


def repartition_macros(kcal, poids_kg, objectif):
    """Répartit les calories en protéines, lipides, glucides.

    Retourne (prot_kcal, lip_kcal, gluc_kcal, avertissements).
    """
    avertissements = []
    ratio = PROT_G_PAR_KG_PERTE if objectif == "perte" else PROT_G_PAR_KG_AUTRE

    prot_kcal = min(ratio * poids_kg * KCAL_PAR_G["prot"], PROT_PART_MAX * kcal)
    lip_kcal = LIPIDES_PART * kcal
    gluc_kcal = kcal - prot_kcal - lip_kcal

    # Contrôle AMDR : les glucides doivent représenter au moins 45 % de l'énergie.
    if gluc_kcal < GLUCIDES_PART_MIN * kcal:
        gluc_kcal = GLUCIDES_PART_MIN * kcal
        prot_kcal = kcal - lip_kcal - gluc_kcal          # 1) on baisse les protéines
        prot_min_kcal = PROT_G_PAR_KG_MIN * poids_kg * KCAL_PAR_G["prot"]
        if prot_kcal < prot_min_kcal:                    # 2) puis les lipides
            prot_kcal = prot_min_kcal
            lip_kcal = max(kcal - prot_kcal - gluc_kcal, LIPIDES_PART_MIN * kcal)
            gluc_kcal = kcal - prot_kcal - lip_kcal
            if gluc_kcal < GLUCIDES_PART_MIN * kcal:
                avertissements.append(
                    "Glucides sous 45 % de l'énergie malgré les corrections."
                )
        else:
            avertissements.append(
                "Protéines réduites pour respecter la plage des glucides (45 % minimum)."
            )

    if gluc_kcal > GLUCIDES_PART_MAX * kcal:
        avertissements.append("Glucides au-dessus de 65 % de l'énergie.")
    return prot_kcal, lip_kcal, gluc_kcal, avertissements


# --------------------------------------------------------------------------
# Fonction principale
# --------------------------------------------------------------------------
def calculer_objectifs(age, sexe, taille_cm, poids_kg, activite, objectif):
    """Calcule les objectifs journaliers. Lève ValueError si une entrée est invalide."""
    valider_entrees(age, sexe, taille_cm, poids_kg, activite, objectif)

    bmr = metabolisme_base(age, sexe, taille_cm, poids_kg)
    tdee = bmr * FACTEURS_ACTIVITE[activite]
    kcal, avertissements = objectif_calorique(tdee, bmr, objectif)

    prot_kcal, lip_kcal, gluc_kcal, av_macros = repartition_macros(kcal, poids_kg, objectif)
    avertissements += av_macros

    if kcal < SEUIL_KCAL_BAS[sexe]:
        avertissements.append(
            "Objectif calorique très bas : avis d'un professionnel de santé recommandé."
        )

    return {
        "kcal": _arrondi(kcal),
        "prot": _arrondi(prot_kcal / KCAL_PAR_G["prot"]),
        "gluc": _arrondi(gluc_kcal / KCAL_PAR_G["gluc"]),
        "lip": _arrondi(lip_kcal / KCAL_PAR_G["lip"]),
        "details": {
            "bmr": round(bmr, 2),
            "tdee": round(tdee, 2),
            "gluc_pourcent": round(100 * gluc_kcal / kcal, 1),
        },
        "avertissements": avertissements,
    }


if __name__ == "__main__":
    exemple = calculer_objectifs(24, "H", 178, 78, "modere", "perte")
    for cle, valeur in exemple.items():
        print(f"{cle:15s} {valeur}")