# TBM — API transports en commun de Bordeaux Métropole

API Python et base PostgreSQL construites sur les données ouvertes GTFS du réseau TBM (Transports Bordeaux Métropole) : arrêts, lignes, horaires, tarifs, recherche des arrêts proches et synchronisation temps réel (GTFS-RT).

## Fonctionnalités
- Import et nettoyage des données GTFS dans PostgreSQL (scripts SQL)
- Recherche géographique des arrêts les plus proches
- API Python (`api.py`)
- Synchronisation des horaires en temps réel (`rt_daemon.py`, `rt_sync*.py`)

## Installation
1. Télécharger le GTFS TBM depuis l'open data de Bordeaux Métropole et placer les fichiers `.txt` à la racine.
2. Créer la base et importer : scripts `tables.sql`, `import.sql`, puis les scripts d'enrichissement.
3. Copier `.env.example` en `.env`, renseigner les valeurs, puis exporter les variables.
4. Lancer l'API : `python api.py`

## Données
Source : réseau TBM — open data Bordeaux Métropole (voir la licence des données sur le portail).
