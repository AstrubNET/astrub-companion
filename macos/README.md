# Installation macOS / MacBook

1. Décompressez l'archive.
2. Faites un clic droit sur `Installer.command`, puis choisissez **Ouvrir**.
3. Si macOS refuse encore l'ouverture, allez dans **Réglages Système > Confidentialité et sécurité**, descendez jusqu'à la section **Sécurité**, puis cliquez sur **Ouvrir quand même** en face de `Installer.command`. Confirmez ensuite avec votre mot de passe ou Touch ID.
4. Sélectionnez votre serveur Dofus dans la liste.
5. Lisez l'écran de transparence et confirmez.
6. Saisissez le mot de passe administrateur du Mac.

Le service `launchd` démarre immédiatement et à chaque démarrage du Mac.

## Commandes fournies

- `Statut.command` : état et derniers événements ;
- `Pause.command` : arrêt temporaire ;
- `Reprendre.command` : reprise de l'écoute ;
- `Desinstaller.command` : suppression du service et des données locales.

Les fichiers sont installés dans `/Library/Application Support/Astrub Companion`. Aucun fichier PCAP n'est enregistré.

## Gatekeeper

Une archive non notariée peut être bloquée par macOS. Essayez d'abord le clic droit **Ouvrir**. Si le bouton n'est pas proposé, tentez une première ouverture, puis allez immédiatement dans **Réglages Système > Confidentialité et sécurité > Sécurité > Ouvrir quand même**. Ne désactivez jamais globalement Gatekeeper.

## Erreur « privilèges d'accès nécessaires »

Cette erreur signifie que le droit d'exécution Unix n'est pas présent sur le fichier. Les archives publiées à partir de la version 1.1.2 conservent automatiquement ce droit. Pour corriger une ancienne archive, ouvrez Terminal, placez-vous dans le dossier décompressé puis exécutez :

```bash
chmod +x *.command *.sh
./Installer.command
```

Vous pouvez également écrire `chmod +x ` (avec un espace), faire glisser `Installer.command` dans la fenêtre Terminal, puis appuyer sur Entrée. Faites ensuite un clic droit sur le fichier et choisissez **Ouvrir**.
