# Installation macOS / MacBook

1. Décompressez l'archive.
2. Faites un clic droit sur `Installer.command`, puis choisissez **Ouvrir**.
3. Sélectionnez votre serveur Dofus dans la liste.
4. Lisez l'écran de transparence et confirmez.
5. Saisissez le mot de passe administrateur du Mac.

Le service `launchd` démarre immédiatement et à chaque démarrage du Mac.

## Commandes fournies

- `Statut.command` : état et derniers événements ;
- `Pause.command` : arrêt temporaire ;
- `Reprendre.command` : reprise de l'écoute ;
- `Desinstaller.command` : suppression du service et des données locales.

Les fichiers sont installés dans `/Library/Application Support/Astrub Companion`. Aucun fichier PCAP n'est enregistré.

## Gatekeeper

Une archive non notariée peut être bloquée par macOS. La version communautaire peut être ouverte avec le clic droit **Ouvrir**. Une signature Developer ID et une notarisation Apple sont prévues pour les versions binaires officielles.
