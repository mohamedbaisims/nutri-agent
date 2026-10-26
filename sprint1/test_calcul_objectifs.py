"""Tests du calcul des objectifs. Lancer avec : python -m unittest -v"""

import unittest

from calcul_objectifs import calculer_objectifs

TOLERANCE = 1  # écart toléré sur chaque valeur (arrondis)

# (description, entrées, valeurs attendues calculées à la main)
PROFILS = [
    (
        "P1 femme, perte (cas limite : glucides à 45,25 %)",
        (30, "F", 165, 60, "leger", "perte"),
        {"kcal": 1452, "prot": 108, "lip": 40, "gluc": 164},
    ),
    (
        "P2 homme, maintien",
        (40, "H", 180, 90, "sedentaire", "maintien"),
        {"kcal": 2196, "prot": 144, "lip": 61, "gluc": 268},
    ),
    (
        "P3 femme, prise de masse",
        (22, "F", 160, 55, "actif", "prise"),
        {"kcal": 2427, "prot": 88, "lip": 67, "gluc": 367},
    ),
    (
        "P4 homme actif, perte (plafond de 500 kcal)",
        (28, "H", 185, 100, "actif", "perte"),
        {"kcal": 2987, "prot": 180, "lip": 83, "gluc": 380},
    ),
    (
        "P5 petite femme, perte (plancher BMR + correction des glucides)",
        (45, "F", 155, 50, "sedentaire", "perte"),
        {"kcal": 1083, "prot": 81, "lip": 30, "gluc": 122},
    ),
]


class TestProfilsDeReference(unittest.TestCase):
    def test_valeurs_attendues(self):
        for description, entrees, attendu in PROFILS:
            with self.subTest(description):
                resultat = calculer_objectifs(*entrees)
                for cle, valeur in attendu.items():
                    self.assertAlmostEqual(
                        resultat[cle], valeur, delta=TOLERANCE,
                        msg=f"{description} : {cle}",
                    )

    def test_coherence_energetique(self):
        """4 x prot + 9 x lip + 4 x gluc doit retomber sur les kcal (arrondis)."""
        for description, entrees, _ in PROFILS:
            with self.subTest(description):
                r = calculer_objectifs(*entrees)
                total = 4 * r["prot"] + 9 * r["lip"] + 4 * r["gluc"]
                self.assertAlmostEqual(total, r["kcal"], delta=10)

    def test_plages_amdr(self):
        for description, entrees, _ in PROFILS:
            with self.subTest(description):
                r = calculer_objectifs(*entrees)
                part = lambda g, k: 100 * g * k / r["kcal"]
                self.assertGreaterEqual(part(r["gluc"], 4), 44.5)
                self.assertLessEqual(part(r["gluc"], 4), 65.5)
                self.assertGreaterEqual(part(r["prot"], 4), 10)
                self.assertLessEqual(part(r["prot"], 4), 35.5)
                self.assertGreaterEqual(part(r["lip"], 9), 19.5)
                self.assertLessEqual(part(r["lip"], 9), 35.5)


class TestGardeFous(unittest.TestCase):
    def test_plafond_du_deficit(self):
        r = calculer_objectifs(28, "H", 185, 100, "actif", "perte")
        self.assertAlmostEqual(r["details"]["tdee"] - r["kcal"], 500, delta=1)

    def test_plancher_bmr(self):
        r = calculer_objectifs(45, "F", 155, 50, "sedentaire", "perte")
        self.assertGreaterEqual(r["kcal"], round(r["details"]["bmr"]))
        self.assertTrue(r["avertissements"])

    def test_maintien_egal_tdee(self):
        r = calculer_objectifs(40, "H", 180, 90, "sedentaire", "maintien")
        self.assertAlmostEqual(r["kcal"], r["details"]["tdee"], delta=1)

    def test_proteines_jamais_sous_le_minimum(self):
        r = calculer_objectifs(45, "F", 155, 50, "sedentaire", "perte")
        self.assertGreaterEqual(r["prot"] / 50, 1.4 - 0.02)


class TestEntreesInvalides(unittest.TestCase):
    def assertRefuse(self, *entrees):
        with self.assertRaises(ValueError):
            calculer_objectifs(*entrees)

    def test_mineur(self):
        self.assertRefuse(17, "H", 178, 78, "modere", "perte")

    def test_sexe_invalide(self):
        self.assertRefuse(24, "X", 178, 78, "modere", "perte")

    def test_poids_negatif(self):
        self.assertRefuse(24, "H", 178, -5, "modere", "perte")

    def test_taille_aberrante(self):
        self.assertRefuse(24, "H", 50, 78, "modere", "perte")

    def test_activite_inconnue(self):
        self.assertRefuse(24, "H", 178, 78, "tres_actif", "perte")

    def test_objectif_inconnu(self):
        self.assertRefuse(24, "H", 178, 78, "modere", "tonifier")

    def test_type_invalide(self):
        self.assertRefuse("24", "H", 178, 78, "modere", "perte")

    def test_perte_refusee_si_imc_trop_bas(self):
        self.assertRefuse(24, "F", 175, 52, "modere", "perte")  # IMC 17,0


if __name__ == "__main__":
    unittest.main()