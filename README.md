## Systeme de detection d'anomalies (Exfiltration Detection)

### Objectif
Surveiller les activites et detecter les comportements anormaux pouvant indiquer une exfiltration de donnees (interne ou externe).

### Contexte et usage
- Sources: logs SIEM, proxies, firewalls, EDR, VPN
- Mode: streaming + analyse quotidienne
- Cible: postes, comptes, serveurs critiques

### Fonctionnalites principales
- Feature engineering automatique (volumes, frequences, destinations)
- Modele non supervise (Isolation Forest)
- Scoring de risque et alertes priorisees
- Baseline par utilisateur, machine et application
- Tableau de bord d'investigation

### Architecture (modules)
- Collecte: agents + ingestion centralisee
- Normalisation: schemas communs et enrichment
- Detection: Isolation Forest + regles metier
- Correlation: score global multi-sources
- Alerting: webhook, email, SIEM

### Flux de traitement
1. Ingestion des logs
2. Normalisation + enrichment
3. Construction des features
4. Scoring d'anomalie
5. Alertes et rapport

### Features types
- Volume de donnees sortantes par fenetre
- Nombre de destinations externes nouvelles
- Horaires inhabituels
- Ratio upload/download
- Acces a donnees sensibles

### Evaluation
- Precision a top-k alertes
- Reduction des faux positifs
- Temps moyen de detection
- Validation par analystes SOC

### Stack proposee
- Python + scikit-learn
- Kafka / Logstash (ingestion)
- Elasticsearch / Kibana (visualisation)
- Postgres (metadonnees)

### Livrables
- Pipeline de detection temps reel
- Tableaux de bord d'alertes
- Regles d'escalade et runbook

### Execution
- Exemple simple: `python exfiltration_detection.py`
- Avec fichier: `python exfiltration_detection.py --input data.json --output alerts.json`
- Ajuster seuil: `--threshold 4.0 --top 5 --no-ml`
- Explications: `--explain`
- Stats: `--stats stats.json`
- Demo: `python exfiltration_detection.py --input data.sample.json --output alerts.json --stats stats.json --explain`
