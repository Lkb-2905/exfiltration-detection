# PRD - Exfiltration Detection

## Vision
Detecter rapidement les comportements d'exfiltration de donnees a partir de logs techniques.

## Probleme
Les alertes classiques sont trop generiques; il faut un scoring comportemental cible.

## Utilisateurs
- Analystes SOC / Blue Team
- RSSI / Security Manager

## MVP (fonctionnalites)
- Ingestion de logs (JSON/JSONL)
- Scoring d'anomalie (robust z-score + regles)
- Alertes JSON triees
- Stats resume (counts, top raisons)

## Evolutions
- Tableau de bord d'investigation
- Correlation multi-sources (proxy, EDR, VPN)
- Mode batch + streaming

## KPI
- Taux de faux positifs
- Temps moyen de detection
- % alertes avec raisons exploitables

## Entrees / Sorties
- Entrees: `data.sample.json` (ou JSONL)
- Sorties: `alerts.json`, `stats.json`

## Contraintes
- Executable en local sans infra lourde
- Reproductibilite des demos

## Hors perimetre
- Orchestration SIEM reelle (ELK, Kafka)
- SOC live 24/7
