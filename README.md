# Projet Big Data HBase-Spark

## Architecture

### Vue d'ensemble
Cluster EMR composé de 3 nœuds :
- 1 Master node (m7g.xlarge) : gestion du cluster et services maîtres
- 2 Core nodes (r7i.xlarge) : stockage HDFS et processing

### Composants
- HBase 2.5.10 : Base de données distribuée pour le stockage
- Spark 3.5.2 : Framework de traitement distribué
- JupyterHub 1.5.0 : Interface de développement
- Livy 0.8.0 : Service REST pour interagir avec Spark
- ZooKeeper 3.9.2 : Coordination du cluster

### Stockage
- HDFS distribué sur les core nodes
- Volumes EBS gp3 :
  - Master : 50 GB
  - Core : 150 GB par nœud

### Accès
- SSH via clé "PolePredict Cluster"
- JupyterHub pour le développement
- Livy pour les jobs Spark

## Installation

### Prérequis
- AWS CLI configuré
- IAM roles pour EMR
- VPC et subnet configurés
- Clé SSH "PolePredict Cluster"

### Déploiement
1. Clone du repository
2. Configuration des variables dans create_cluster.sh
3. Exécution du script