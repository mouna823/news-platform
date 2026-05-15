# News Platform — Architecture de Données Big Data

> Plateforme de collecte, traitement et analyse d'articles de presse en temps réel

## Aperçu

Ce projet implémente une architecture Big Data complète pour collecter automatiquement des articles depuis des sites d'actualité marocains et internationaux, les stocker dans un Data Lake selon l'architecture Médaillon, et visualiser les tendances médiatiques via des dashboards interactifs.

---

## Architecture

```
Sources Web
    │
    ├── Hespress (RSS)
    ├── Al Jazeera (AR + EN)
    └── BBC News
         │
         ▼
    ┌─────────────────────────────────────┐
    │           INGESTION                 │
    │  Batch (Airflow, 1h)                │
    │  Streaming (Kafka + Consumer)       │
    └────────────────┬────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────┐
    │        DATA LAKE — MinIO            │
    │                                     │
    │  🥉 Bronze  →  données brutes       │
    │  🥈 Silver  →  nettoyées            │
    │  🥇 Gold    →  agrégées             │
    └────────────────┬────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────┐
    │      DATA WAREHOUSE — PostgreSQL    │
    │  articles · articles_per_source     │
    │  top_keywords · data_quality_log    │
    └────────────────┬────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────┐
    │       VISUALISATION — Grafana       │
    │  Tendances · Sources · Mots-clés    │
    └─────────────────────────────────────┘
```

---

## Technologies utilisées

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Scraping | Python, BeautifulSoup, RSS | Collecte automatique des articles |
| Streaming | Apache Kafka | Bus d'événements temps réel |
| Orchestration | Apache Airflow | Planification et supervision du pipeline |
| Data Lake | MinIO (S3-compatible) | Stockage distribué Bronze/Silver/Gold |
| Data Warehouse | PostgreSQL | Tables analytiques pour les dashboards |
| Visualisation | Grafana | Dashboards et indicateurs clés |
| Monitoring | Prometheus | Métriques des services |
| Déploiement | Docker, Kubernetes | Conteneurisation et scalabilité |

---

## Structure du projet

```
news-platform/
│
├── scrapers/                          # Web scrapers
│   ├── base_scraper.py                # Classe de base commune
│   ├── hespress_scraper.py            # Scraper Hespress (RSS)
│   ├── aljazeera_scraper.py           # Scraper Al Jazeera AR/EN
│   └── bbc_scraper.py                 # Scraper BBC News
│
├── ingestion/
│   └── kafka/
│       ├── producer.py                # Envoi des articles vers Kafka
│       └── consumer.py                # Consommation temps réel
│
├── datalake/
│   └── bronze/
│       └── writer.py                  # Écriture dans MinIO Bronze
│
├── processing/
│   ├── bronze_to_silver/
│   │   └── transformer.py             # Nettoyage et normalisation
│   └── silver_to_gold/
│       └── aggregator.py              # Agrégations analytiques
│
├── pipeline/
│   └── airflow/
│       └── dags/
│           └── news_pipeline_dag.py   # DAG Airflow (pipeline horaire)
│
├── warehouse/
│   └── sql/
│       └── init.sql                   # Schéma PostgreSQL
│
├── quality/
│   └── checker.py                     # Contrôles qualité des données
│
├── monitoring/
│   ├── prometheus.yml                 # Configuration Prometheus
│   └── grafana/                       # Dashboards et datasources
│
├── deployment/
│   └── kubernetes/                    # Manifests K8s (7 fichiers YAML)
│
├── run_scraper.py                     # Lance les scrapers
├── run_bronze_silver.py               # Pipeline Bronze → Silver
├── run_gold.py                        # Pipeline Silver → Gold
├── run_quality.py                     # Rapport qualité
├── Dockerfile.airflow                 # Image Airflow personnalisée
├── docker-compose.yml                 # Tous les services Docker
└── requirements.txt                   # Dépendances Python
```

---

## Démarrage rapide

### Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré
- Python 3.10+
- Git

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/mouna823/news-platform.git
cd news-platform

# 2. Construire l'image Airflow avec les dépendances
docker-compose build

# 3. Lancer tous les services
docker-compose up -d

# 4. Vérifier que tout tourne
docker-compose ps

# 5. Installer les dépendances Python locales
pip install -r requirements.txt
```

### Lancer le pipeline

```bash
# Scraping des articles
python run_scraper.py all

# Transformation Bronze → Silver
python run_bronze_silver.py

# Agrégation Silver → Gold
python run_gold.py

# Rapport de qualité
python run_quality.py
```

---

## Accès aux interfaces

| Interface | URL | Identifiants |
|-----------|-----|-------------|
| Airflow | http://localhost:8081 | admin / admin123 |
| MinIO | http://localhost:9001 | admin / admin12345 |
| Kafka UI | http://localhost:8080 | — |
| Grafana | http://localhost:3000 | admin / admin123 |
| Prometheus | http://localhost:9090 | — |

---

## Architecture Médaillon

### 🥉 Bronze — Données brutes
- Stockage tel quel, aucune transformation
- Format JSON avec HTML conservé
- Partitionné : `layer=batch/source=BBC/year=2025/month=05/day=14/`

### 🥈 Silver — Données nettoyées
- Suppression des balises HTML
- Normalisation du texte et des espaces
- Détection automatique de la langue (`langdetect`)
- Déduplication par hash MD5 du contenu
- Validation : titre, contenu > 100 caractères, date valide

### 🥇 Gold — Données agrégées
- Top 50 mots-clés les plus fréquents
- Nombre d'articles par source
- Répartition par catégorie
- Insertion dans PostgreSQL pour Grafana

---

## Qualité des données

Trois dimensions contrôlées à chaque run :

| Dimension | Contrôles |
|-----------|-----------|
| Complétude | Titre, URL, source, date présents |
| Validité | Contenu > 100 chars, date non future, langue reconnue |
| Cohérence | word_count cohérent, source correspond à l'URL |

Seuil d'alerte : pipeline échoue si taux d'erreur > 30%

---

## Déploiement Kubernetes (production)

```bash
# Appliquer tous les manifests
kubectl apply -f deployment/kubernetes/

# Vérifier les pods
kubectl get pods -n news-platform

# Accéder à Airflow
kubectl port-forward svc/airflow-webserver 8081:8080 -n news-platform
```

---

## Sources d'actualité

| Site | Pays | Langue | Méthode |
|------|-------|--------|---------|
| Hespress | Maroc | Arabe | RSS Feed |
| Al Jazeera | Qatar | Arabe + Anglais | HTML scraping |
| BBC News | Royaume-Uni | Anglais | HTML scraping |

---

## Auteur

Projet réalisé dans le cadre du cours **Architecture de Données**  
**Mouna** — 2025
