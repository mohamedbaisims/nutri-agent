# nutri-agent

Agent IA nutritionnel : l'utilisateur photographie son assiette, l'application identifie les aliments, calcule les calories et les macronutriments, indique ce qui reste pour la journée et propose une alternative plus saine si besoin.

Technologies prévues : n8n (orchestration), PostgreSQL + pgvector (données et RAG), segmentation d'images (FoodSeg103), estimation des grammes (Nutrition5k), agent LLM et prompt engineering.

> Les estimations nutritionnelles sont indicatives et ne constituent pas un avis médical.

## Prérequis

- Docker Desktop (lancé avant toute commande `docker`)
- Git

## Démarrage

```
copy .env.example .env
docker compose up -d
docker compose ps
```

Avant de lancer, édite `.env` et remplace :

- `POSTGRES_PASSWORD` par un vrai mot de passe
- `N8N_ENCRYPTION_KEY` par une clé aléatoire, générée avec :
  `python -c "import secrets; print(secrets.token_hex(24))"`

Le fichier `.env` est ignoré par Git : ne le publie jamais.

| Service | Adresse |
|---|---|
| n8n | http://localhost:5678 (créer le compte propriétaire au premier accès) |
| PostgreSQL + pgvector | localhost:5432, base `nutri_agent` |

## Vérifier l'installation

`docker compose ps` doit afficher `nutri_db` en `healthy` et `nutri_n8n` en `Up`. Ensuite :

```
docker compose exec db psql -U nutri -d nutri_agent -c "\dt"
docker compose exec db psql -U nutri -d nutri_agent -c "\dv"
```

Résultat attendu :

- 5 tables : `users`, `meals`, `meal_items`, `nutrition_ref`, `dishes_ref`
- 2 vues : `v_daily_totals`, `v_daily_remaining`

Si ton `POSTGRES_USER` n'est pas `nutri`, remplace-le dans les commandes.

## Structure du dépôt

```
nutri-agent/
├── data/            scripts de téléchargement des datasets, mapping des classes
├── notebooks/       segmentation, estimation des grammes, évaluation
├── vision_api/      API FastAPI (segmentation et grammes)
├── db/init/         scripts SQL exécutés au premier démarrage de la base
├── n8n/             workflows n8n exportés en JSON
├── prompts/         prompt système de l'agent et jeux de tests
├── eval/            jeu de test réel et scripts de métriques
├── docker-compose.yml
├── .env.example     modèle des variables d'environnement
└── .gitignore
```

## Modèle de données

| Objet | Rôle |
|---|---|
| `users` | Profil (âge, sexe, taille, poids, activité, objectif) et objectifs journaliers |
| `meals` | Un repas = une photo analysée, avec les totaux kcal, protéines, glucides, lipides |
| `meal_items` | Détail d'un repas : un aliment et ses grammes par ligne |
| `nutrition_ref` | Valeurs pour 100 g par aliment, avec embedding (base du RAG) |
| `dishes_ref` | Plats de référence pour proposer des alternatives plus saines |
| `v_daily_totals` | Somme des repas par utilisateur et par jour |
| `v_daily_remaining` | Reste du jour : objectif moins total consommé |

Le compteur du jour n'est jamais stocké : il est calculé par les vues à partir des repas. Chaque nouveau jour repart donc automatiquement à zéro. Le jour est défini dans le fuseau `Africa/Tunis`.

Les embeddings ont 768 dimensions (modèle `multilingual-e5-base`).

## Réinitialiser la base

Les scripts de `db/init/` ne s'exécutent qu'au **premier** démarrage, sur un volume vide. Après toute modification du schéma SQL, il faut donc repartir de zéro :

```
docker compose down -v
docker compose up -d
```

Attention : l'option `-v` supprime les volumes, donc **toutes les données** de PostgreSQL et de n8n (workflows, comptes). À n'utiliser qu'en développement.

## Dépannage

| Symptôme | Cause probable |
|---|---|
| `nutri_db` est `unhealthy` | Erreur dans un script de `db/init/` : `docker compose logs db --tail 40` |
| La base `n8n` n'existe pas | `db/init/01_create_n8n_db.sql` absent ou mal nommé, puis `down -v` |
| `port is already allocated` | Un autre service utilise le port 5432 ou 5678 : changer le port à gauche dans `docker-compose.yml` |
| `docker : ... pipe ... not found` | Docker Desktop n'est pas lancé |
| `psql` non reconnu | Normal : `psql` tourne dans le conteneur, utiliser `docker compose exec db psql ...` |

## Méthode : Scrum, module par module

Chaque module est un sprint avec une Definition of Done vérifiable. On ne passe au suivant que lorsqu'elle est atteinte.

| Sprint | Module | Statut |
|---|---|---|
| 0 | Cadrage et socle | Terminé |
| 1 | Profil et objectifs journaliers | À faire |
| 2 | Base nutritionnelle et RAG | À faire |
| 3 | Segmentation (FoodSeg103) | À faire |
| 4 | Estimation des grammes (Nutrition5k) | À faire |
| 5 | API Vision | À faire |
| 6 | Workflow repas et verdict | À faire |
| 7 | Agent LLM, prompts et alternatives | À faire |
| 8 | Évaluation et rapport | À faire |

### Definition of Done du Sprint 0

- [x] Dépôt structuré avec `.gitignore` et `.env.example`
- [x] `docker compose up -d` démarre n8n et PostgreSQL avec pgvector
- [x] Schéma SQL créé automatiquement (5 tables, 2 vues)
- [x] README rédigé
- [ ] Premier commit Git