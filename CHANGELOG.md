# Historique

## 1.1.3

- compatibilité avec les nouveaux messages HDV `kde` et `jzn` ;
- conservation de la compatibilité avec les anciens messages `keh` et `kbt` ;
- correction de la détection des consultations de prix après la mise à jour Dofus.
- vérification automatique quotidienne sous Windows et toutes les six heures sous macOS ;
- notification native lorsqu'une nouvelle release stable est disponible ;
- commande manuelle de recherche de mise à jour sur les deux plateformes.

## 1.1.2

- droits d'exécution des commandes macOS préservés dans l'archive publiée ;
- procédure Gatekeeper détaillée dans le README, la documentation macOS et la FAQ ;
- commande de réparation `chmod +x` documentée pour les anciennes archives.

## 1.1.1

- encodage UTF-8 corrigé pour Windows PowerShell 5.1, les journaux et les consoles ;
- téléchargement et lancement guidé de l'installateur officiel signé Npcap lorsqu'il est absent.

## 1.1.0

- version Windows ouverte et non obfusquée ;
- capture passive multi-interface via Npcap ;
- installateur graphique et démarrage automatique ;
- compilation reproductible de l'exécutable Windows avec GitHub Actions.

## 1.0.0

- installateur macOS avec sélection graphique du serveur ;
- liste des serveurs récupérée depuis Astrub.net ;
- contribution anonyme sans compte ni token ;
- interface réseau détectée automatiquement ;
- UUID d'installation aléatoire stocké sous forme de hash côté API ;
- suppression des identifiants techniques d'offre avant transmission ;
- commandes graphiques de statut, pause, reprise et désinstallation ;
- documentation publique de confidentialité, sécurité et architecture.
