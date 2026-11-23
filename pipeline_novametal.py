# -*- coding: utf-8 -*-
"""
Pipeline Data NOVAMETAL — Bronze -> Silver -> Gold
Source : les enregistrements réels du POC Odoo (novametal.odoo.com),
exportés en CSV (couche Bronze). En entreprise, la Bronze serait
alimentée par l'API Odoo / un connecteur vers la base PostgreSQL.
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
BRONZE, SILVER, GOLD = BASE / "bronze", BASE / "silver", BASE / "gold"
SILVER.mkdir(exist_ok=True)
GOLD.mkdir(exist_ok=True)

# ---------------- BRONZE (données brutes, telles qu'exportées d'Odoo) -------
produits = pd.read_csv(BRONZE / "produits.csv")
achats = pd.read_csv(BRONZE / "achats_P00001.csv")
nomen = pd.read_csv(BRONZE / "nomenclature_RACK.csv")
mouvements = pd.read_csv(BRONZE / "mouvements_stock.csv")
ventes = pd.read_csv(BRONZE / "ventes_S00001.csv")

# ---------------- SILVER (nettoyé, enrichi, valorisé) ----------------------
prix = produits.set_index("ref_produit")["prix_achat_dh"].to_dict()

# Coût de revient du produit fini, calculé depuis la nomenclature (BoM)
nomen["cout_composant"] = nomen.apply(
    lambda r: r["quantite_par_unite"] * prix[r["ref_composant"]], axis=1)
cout_revient = nomen.groupby("produit_fini")["cout_composant"].sum().to_dict()
cout_unitaire = dict(prix)
cout_unitaire.update(cout_revient)  # RACK -> 1700 DH

# Fait stock : chaque mouvement valorisé au coût
fait = mouvements.copy()
fait["cout_unitaire_dh"] = fait["ref_produit"].map(cout_unitaire)
fait["valeur_mouvement_dh"] = fait["quantite"] * fait["cout_unitaire_dh"]
fait = fait.merge(produits[["ref_produit", "nom_produit"]], on="ref_produit")
fait.to_csv(SILVER / "fait_mouvements_stock.csv", index=False)

# ---------------- GOLD (tables de décision) --------------------------------
# 1) Marge par produit vendu
v = ventes.merge(
    pd.Series(cout_unitaire, name="cout_revient_unitaire_dh"),
    left_on="ref_produit", right_index=True)
v["marge_unitaire_dh"] = v["prix_unitaire_dh"] - v["cout_revient_unitaire_dh"]
v["marge_totale_dh"] = v["marge_unitaire_dh"] * v["quantite"]
v["marge_pct"] = (v["marge_unitaire_dh"] / v["prix_unitaire_dh"] * 100).round(1)
gold_marge = v[["ref_produit", "quantite", "prix_unitaire_dh",
                "cout_revient_unitaire_dh", "marge_unitaire_dh",
                "marge_totale_dh", "marge_pct", "montant_dh"]]
gold_marge.to_csv(GOLD / "gold_marge_produit.csv", index=False)

# 2) Stock actuel + alertes de réapprovisionnement (seuil = paramètre métier)
SEUIL_MIN = {"TOLE": 10, "TUBE": 10, "VISS": 10, "PEIN": 10, "RACK": 0}
stock = fait.groupby(["ref_produit", "nom_produit"], as_index=False)["quantite"].sum()
stock["valeur_stock_dh"] = stock.apply(
    lambda r: r["quantite"] * cout_unitaire[r["ref_produit"]], axis=1)
stock["seuil_min"] = stock["ref_produit"].map(SEUIL_MIN)

def statut(r):
    if r["quantite"] == 0 and r["ref_produit"] == "PEIN":
        return "RUPTURE - réapprovisionner"
    if r["quantite"] == 0:
        return "Écoulé (commande livrée)"
    if r["quantite"] <= r["seuil_min"]:
        return "LIMITE - surveiller"
    return "OK"
stock["statut"] = stock.apply(statut, axis=1)
stock.to_csv(GOLD / "gold_stock_alertes.csv", index=False)

# 3) Synthèse du flux complet
synthese = pd.DataFrame([
    ["Achats P00001 (matières premières)", achats["montant_dh"].sum()],
    ["Production WH/MO/00001 (composants consommés)",
     -fait.query("type_mouvement=='consommation'")["valeur_mouvement_dh"].sum()],
    ["Ventes S00001 (facture INV/2026/00001 PAYÉE)", ventes["montant_dh"].sum()],
    ["Marge brute du flux", v["marge_totale_dh"].sum()],
    ["Valeur du stock final", stock["valeur_stock_dh"].sum()],
], columns=["indicateur", "montant_dh"])
synthese.to_csv(GOLD / "gold_synthese_flux.csv", index=False)

print("Coût de revient RACK :", cout_unitaire["RACK"], "DH")
print(synthese.to_string(index=False))
print(stock[["ref_produit", "quantite", "valeur_stock_dh", "statut"]].to_string(index=False))
print(gold_marge.to_string(index=False))
