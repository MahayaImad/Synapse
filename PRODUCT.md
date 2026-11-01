# Product

<!-- impeccable:product-schema 1 -->

## Platform

android

## Stack

Flutter (Android d'abord, iOS ensuite), nomenclature embarquée en SQLite avec recherche plein texte (FTS5), conformément au cahier des charges. Backend d'administration existant : `backend/` (Python, `synapse-admin`).

## Users

Pharmaciens d'officine algériens et leurs assistants, au comptoir, face au patient, souvent d'une seule main, ordonnance (souvent manuscrite) dans l'autre. Leur travail : retrouver vite le produit exact prescrit (marque, dosage, forme) dans la nomenclature nationale, vérifier son statut et ses équivalents avant la délivrance. Médecins en V2 ; grand public exclu.

## Product Purpose

Synapse aide le pharmacien à lire une ordonnance, à retrouver chaque médicament dans la nomenclature algérienne et à repérer les risques avant la délivrance. Objectif final : une ordonnance photographiée devient en moins de 30 s une liste de produits vérifiés avec les alertes utiles.

Premier jalon de l'app (en cours) : recherche hors connexion dans la nomenclature, fiche produit (DCI, statut en vigueur / non renouvelé / retiré, liste I / liste II / stupéfiant, équivalents de même code DCI) et mise à jour automatique du fichier de nomenclature.

## Positioning

Les données viennent de la nomenclature officielle du ministère, importée chaque mois, versionnée et validée par un administrateur ; chaque information affichée est traçable jusqu'à sa version. Le LLM (phases suivantes) lit et reformule seulement : identification, interactions et doses sont décidées par des données sourcées et des règles déterministes. Le pharmacien valide toujours.

## Operating Context

- Comptoir d'officine : usage rapide, interruptions, une main, lumière variable, réseau parfois absent.
- La nomenclature est publiée chaque mois (fichier Excel du ministère) ; l'admin l'importe et publie un fichier SQLite + `manifest.json` (`synapse-admin publish`).
- Le pharmacien ne gère pas les mises à jour : elles arrivent seules.

## Capabilities and Constraints

- Recherche locale < 300 ms, toujours disponible hors connexion.
- L'APK embarque la dernière nomenclature publiée ; l'app lit `manifest.json` à une URL configurable (hébergement statique en attendant le serveur en Algérie) et télécharge le nouveau fichier, vérifié par SHA-256.
- Les produits retirés et non renouvelés restent consultables, toujours affichés avec leur statut (une ordonnance peut citer une ancienne marque).
- Données de nomenclature en français, en majuscules, telles que publiées par le ministère (abréviations comprises : « SOL. INJ. », « B/30 »…).
- Interface : français seulement pour ce jalon ; chaînes externalisées pour ajouter l'arabe (RTL) ensuite.
- Hors périmètre de ce jalon : photo d'ordonnance, lecture LLM, interactions, posologie pédiatrique.
- Aucune donnée patient dans ce jalon.

## Brand Commitments

Nom : Synapse (startup Synapse). Outil d'aide à la dispensation : la décision reste au pharmacien.

Direction visuelle choisie par l'utilisateur (après deux tirages) : Material 3 standard, joué franchement, sans signature propre ; référence de finition : les apps Google (Contacts, Fichiers, Agenda).

## Evidence on Hand

Nomenclature réelle publiée par `synapse-admin` (≈ 9 500 produits, versions 2024-08 à 2026-08). Aucun logo, aucune charte graphique, aucun témoignage : ne pas en inventer.

## Product Principles

1. Le statut d'un produit n'est jamais ambigu : retiré ou non renouvelé se voit avant tout le reste.
2. Ce qui est affiché vient de la nomenclature, avec sa version ; rien n'est deviné.
3. Rapidité au comptoir : le bon produit en quelques frappes, d'une main.
4. Hors connexion par défaut ; le réseau n'est qu'un bonus pour les mises à jour.

## Accessibility & Inclusion

Utilisable d'une main ; texte agrandissable (respect de la taille de police système) ; arabe affiché de droite à gauche quand il arrivera (prévoir le RTL dès la structure).
