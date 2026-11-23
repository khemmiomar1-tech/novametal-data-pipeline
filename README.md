# NOVAMETAL Data Pipeline — Bronze → Silver → Gold (pandas)

A small, complete Data Engineering pipeline built for a **proof of concept
(POC)** with NOVAMETAL, a steel-products company: raw exports from the
**Odoo ERP** are turned into decision-ready tables for **Power BI**.

## What the pipeline does

```
Odoo ERP exports (CSV)          BRONZE   raw data, exactly as exported
        |                       ─────────────────────────────────────────
        v  pipeline_novametal.py
Stock movements valued at cost  SILVER   fait_mouvements_stock.csv
        |                       ─────────────────────────────────────────
        v
Margin per product              GOLD     gold_marge_produit.csv
Stock levels + reorder alerts   GOLD     gold_stock_alertes.csv
End-to-end flow summary         GOLD     gold_synthese_flux.csv
        |
        v
Power BI dashboard (DAX measures in Mesures_DAX_PowerBI.txt,
build guide in Guide_PowerBI_NOVAMETAL.txt)
```

**Key business logic**

- **Cost of goods from the bill of materials (BoM):** the finished product's
  unit cost is computed from its nomenclature — quantity per unit × purchase
  price of each component.
- **Stock-movement valuation:** every stock movement is valued at that cost,
  producing a valued stock fact table in Silver.
- **Gold decision tables:** margin per product sold, current stock with
  minimum-threshold reorder alerts, and a full flow summary (purchases →
  production consumption → sales → gross margin → final stock value).

## Run it

```bash
pip install pandas
python pipeline_novametal.py
```

The script reads `bronze/`, rewrites `silver/` and `gold/`, and prints the
flow summary. In a production setting, the Bronze layer would be fed by the
Odoo API or a connector to its PostgreSQL database instead of CSV exports.

## Stack

Python · pandas · Odoo ERP (source) · Power BI / DAX

## Résumé (Français)

Pipeline de données Bronze → Silver → Gold en pandas, réalisé pour un POC
avec NOVAMETAL (produits en acier) : exports CSV de l'ERP Odoo en Bronze,
valorisation des mouvements de stock au coût de revient calculé depuis la
nomenclature (BoM) en Silver, et tables de décision Gold pour Power BI —
marge par produit, alertes de stock et synthèse du flux complet.

---
Omar Khemmi — Data Engineer — Casablanca, Morocco
