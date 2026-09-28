<!-- Built: tokens below survived the first implementation pass (static/stylesheets/ligue/*.css). -->

---
name: Ligue des Pamplemousses — site public
description: La table de marque d'un match d'improv, mise en page pour le web.
colors:
  ardoise: "#15181C"
  ardoise-carte: "#1E2227"
  encre: "#F4F2ED"
  encre-att: "#9AA1AA"
  liseret: "rgb(244 242 237 / 10%)"
  pamplemousse: "#F05D5F"
  tangerine: "#F48E42"
  clementine: "#F7B12F"
  carton-jaune: "#FFC94A"
typography:
  display:
    fontFamily: "Maven Pro, sans-serif"
    fontWeight: 900
    letterSpacing: "-0.01em"
  label:
    fontFamily: "Maven Pro, sans-serif"
    fontWeight: 700
    letterSpacing: "0.08em"
  body:
    fontFamily: "Maven Pro, sans-serif"
    fontWeight: 400
rounded:
  card: "0.85rem"
  patch: "999px"
spacing:
  sm: "0.75rem"
  md: "1.25rem"
  lg: "2rem"
  xl: "3.5rem"
---

# Design System: Ligue des Pamplemousses — site public

## Overview

**Creative North Star: "La table de marque"**

Le site public se met en scène comme si le visiteur regardait par-dessus l'épaule de l'arbitre, à la table de marque, pendant un match d'impro : les statuts se lisent en langage de carton (jaune = à venir, sifflet final = joué), les chiffres de pointage occupent l'espace comme sur un tableau, et chaque carte — équipe, document, membre du CA — est posée sur la table comme une carte qu'on tient en main, avec un liseré de couleur de division sur le bord.

Ce monde évite les deux pièges génériques de l'IA : ni fond crème/serif chaleureux, ni néon sur noir absolu avec effet de lueur. Le fond est un ardoise presque noir mais chaud (pas de noir pur), et les couleurs d'agrumes occupent de vrais aplats pleins (30 à 60 % d'un viewport) plutôt que de servir de simples accents.

**Key Characteristics:**
- Fond ardoise chaud presque noir comme structure ; couleurs d'agrumes en aplats pleins, jamais en accents seuls.
- Cartes = objets physiques tenus en main (ombre portée dure, pas de flou doux).
- Statuts communiqués en langage d'arbitrage (carton jaune / sifflet final), jamais en vert/rouge générique de dashboard.
- Équipes sans logo reçoivent un écusson numéroté façon chandail plutôt qu'un espace vide.
- Un seul séparateur signature : le cordon de sifflet (ligne en boucles), utilisé avec parcimonie.

## Colors

Fond structurel sombre et chaud ; les trois couleurs d'agrumes sont les seules couleurs saturées du système et ne servent jamais de décor — chacune EST la couleur d'une division entière.

### Primary
- **Pamplemousse** (#F05D5F) : couleur pleine de la division Pamplemousse — hero, bandeau de section, liseré des cartes de cette division.
- **Tangerine** (#F48E42) : idem pour la division Tangerine.
- **Clémentine** (#F7B12F) : idem pour la division Clémentine.

### Secondary
- **Carton jaune** (#FFC94A) : réservé exclusivement au badge de statut « à venir ». N'est jamais utilisé comme couleur de division, même sur les pages Clémentine — sa fonction est le statut, pas la marque.

### Neutral
- **Ardoise** (#15181C) : fond de structure (corps de page, nav, footer).
- **Ardoise carte** (#1E2227) : fond des cartes et tableaux, un cran plus clair que le fond de page pour suggérer une carte posée sur la table.
- **Encre** (#F4F2ED) : texte principal sur fond sombre — blanc cassé chaud, jamais blanc pur.
- **Encre atténuée** (#9AA1AA) : texte secondaire, légendes, libellés de tableau.
- **Liseret** (rgb(244 242 237 / 10%)) : lignes de séparation, bordures de tableau — jamais une couleur opaque dédiée.

### Named Rules
**La règle du carton.** Le jaune-carton ne sert qu'au statut « à venir ». Il n'apparaît jamais comme couleur de division, même sur les pages Clémentine — s'il colore autre chose qu'un badge de statut, c'est une erreur.

**La règle de l'aplat.** Une couleur de division occupe toujours un vrai champ plein (bandeau, fond de section, carte) sur au moins 30 % du viewport de la page qu'elle identifie — jamais seulement une bordure de 2px ou une icône.

**La règle de l'encre foncée.** Sur toute surface dont le fond est un aplat de couleur de division (claire et saturée), le texte est en `--color-ardoise` (encre foncée), jamais en `--color-encre` (blanc cassé) — le contraste est plus fiable et le rendu évoque un tampon encreur sur une étiquette de caisse d'agrumes. Sur les surfaces neutres (`--color-ardoise` / `--color-ardoise-carte`), c'est l'inverse : texte en `--color-encre`.

## Typography

**Display Font:** Maven Pro (variable, 400–900)
**Body Font:** Maven Pro (400–500)
**Label Font:** Maven Pro (700, majuscules, tracking large)

**Character:** Une seule famille, mais des extrêmes de graisse marqués — le 900 (Black) porte les gros chiffres façon tableau de pointage et les titres, le 400 porte le texte courant. La hiérarchie vient du poids et de l'échelle, jamais d'un second caractère.

### Hierarchy
- **Display** (900, `clamp(2rem, 1.3rem + 3vw, 3.5rem)`, 1.05) : titres de hero, chiffres de classement/score à grande échelle.
- **Headline** (800, `clamp(1.5rem, 1.1rem + 2vw, 2.25rem)`) : titres de page.
- **Title** (700, 1.1rem) : titres de carte, noms d'équipe.
- **Body** (400, 1rem, 1.6) : texte courant, 65ch max.
- **Label** (700, 0.75rem, tracking 0.08em, majuscules) : libellés de tableau, badges de statut.

### Named Rules
**La règle du seul caractère.** Une seule famille (Maven Pro) sur tout le site public — la hiérarchie se construit avec le poids, l'échelle et l'espacement, jamais avec une seconde police.

## Layout

Mobile-first, conteneur principal max `75rem` centré. La nav est une console fixe en haut de page (« table de marque ») qui bascule en tiroir hamburger sous `64rem`. Chaque page de division ouvre sur un bandeau plein de la couleur de division (pas un simple bandeau d'accent) avant tout contenu neutre. Rythme d'espacement en paliers (`0.75 / 1.25 / 2 / 3.5rem`), plus d'espace au-dessus d'un titre qu'en dessous.

## Elevation & Depth

Pas d'ombres douces ni de flou ambiant. La profondeur vient d'un ombrage dur et décalé (« carte tenue en main ») : un décalage net, sans flou, qui suggère un objet physique légèrement soulevé de la table plutôt qu'un flottement numérique.

### Shadow Vocabulary
- **carte-tenue** (`box-shadow: 0.25rem 0.25rem 0 rgb(0 0 0 / 35%)`) : ombre par défaut de toute carte (équipe, document, membre du CA).
- **carte-survolée** (`box-shadow: 0.4rem 0.4rem 0 rgb(0 0 0 / 40%); transform: translate(-0.15rem, -0.15rem)`) : état hover/focus — la carte se soulève un peu plus.

### Named Rules
**La règle de l'ombre dure.** Jamais de `box-shadow` flou/diffus. Toujours un décalage net sans flou (0 de blur) — c'est la signature du système, pas un oubli d'optimisation.

## Shapes

Module de base : rectangle à coins adoucis (`0.85rem`) avec un liseré de couleur de division sur le bord supérieur (`0.3rem`). Les marques d'équipe sans logo utilisent un écusson circulaire (`rounded.patch`, 999px) avec le numéro ou les initiales de l'équipe — jamais un rectangle gris vide. Le quartier d'agrume du logo CITRUS (segments géométriques en éventail) réapparaît en accent discret sur le hero d'accueil uniquement, jamais répété partout.

## Components

### Navigation
Console fixe façon table de marque : fond ardoise, item de division actif souligné dans sa couleur. Les dropdowns de division s'ouvrent avec un liseré supérieur de la couleur de division. L'onglet Tournoi désactivé reste visuellement présent mais assourdi (opacité réduite, `cursor: not-allowed`). Le lien Citrus se distingue par un fond en dégradé des trois couleurs d'agrumes.

### Chips (badges de statut)
- **À venir** : fond carton-jaune (#FFC94A), texte ardoise, coins arrondis en pilule.
- **Joué** : marqueur « sifflet final » en encre atténuée, jamais coloré — un match joué n'est pas un statut à célébrer visuellement, juste un fait consigné.

### Cards / Containers
- **Coins :** `0.85rem`.
- **Fond :** ardoise-carte (#1E2227).
- **Ombre :** carte-tenue / carte-survolée (voir Elevation).
- **Bordure :** liseret de division en haut, `0.3rem`.
- **Padding interne :** palier `md` (1.25rem) à `lg` (2rem) selon densité de contenu.

### Tableaux (calendrier / classement)
Chiffres en `font-variant-numeric: tabular-nums`, poids 900 pour les colonnes de score/points. En-têtes en Label (majuscules, tracking large, encre atténuée). Lignes séparées par le liseret, jamais par une bordure opaque.

### Séparateur signature
Le cordon de sifflet : une ligne en boucles (`repeating` motif léger) utilisée entre les grandes sections d'une page — jamais plus d'une fois par page, sinon elle perd son statut de signature.

## Do's and Don'ts

### Do:
- **Do** traiter chaque couleur de division comme un aplat plein occupant une vraie surface, pas un accent.
- **Do** donner à chaque équipe sans logo un écusson numéroté plutôt qu'un espace vide.
- **Do** garder l'ombre dure et décalée comme seule forme de profondeur.

### Don't:
- **Don't** utiliser de fond crème/ivoire ou de serif display — ce n'est pas la direction retenue (rejetée explicitement lors du choix de direction).
- **Don't** utiliser de néon sur noir pur avec effet de lueur — rejeté pour la même raison.
- **Don't** utiliser le jaune-carton comme couleur de division ou de décor — il est réservé au statut « à venir ».
- **Don't** utiliser des dégradés pastel doux ou des formes de blob arrondies — évoque le générique « startup IA », rejeté par le produit.
