# Astrub Companion pour Windows

## Installation

1. Double-cliquez sur `Installer.cmd` et acceptez la demande administrateur.
2. Si Npcap est absent, Astrub Companion télécharge son installateur signé directement depuis `npcap.com`. Validez simplement son assistant officiel.
3. Choisissez votre serveur Dofus puis cliquez sur **J'accepte**.

L'installation privilégie `AstrubCompanion.exe` lorsqu'il est placé dans ce dossier. À défaut, elle exécute directement le fichier source avec Python 3. Le comportement est identique.

## Contrôle

- `Statut.cmd` affiche l'état et les vingt dernières lignes du journal ;
- `Pause.cmd` interrompt la collecte et désactive son démarrage ;
- `Reprendre.cmd` réactive et relance la collecte ;
- `Desinstaller.cmd` retire le programme et ses données locales.
- `RechercherUneMiseAJour.cmd` vérifie immédiatement la dernière release stable.

Les fichiers locaux se trouvent dans `C:\ProgramData\Astrub Companion`. Aucun paquet capturé n'est enregistré sur le disque.

## Exécutable reproductible

Le workflow `.github/workflows/tests.yml` compile `AstrubCompanion.exe` avec PyInstaller à chaque exécution. L'exécutable n'est pas obfusqué : le fichier Python qui fait foi reste fourni et chaque build peut être reproduit depuis le dépôt.

Npcap est un composant séparé distribué selon sa propre licence. Il n'est pas intégré ni redistribué dans cette archive : l'utilisateur le télécharge directement depuis le site officiel. L'installation réellement silencieuse est réservée à Npcap OEM.

## Mises à jour

Une tâche utilisateur vérifie GitHub à l'ouverture de session et chaque jour. Lorsqu'une version stable plus récente est disponible, Windows propose d'ouvrir la release officielle. Aucun paquet provenant d'un autre domaine n'est accepté et aucune installation administrative silencieuse n'est effectuée.
