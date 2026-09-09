# Contribuer

Les correctifs, tests et audits de confidentialité sont bienvenus. Toute modification doit conserver les principes suivants : écoute passive uniquement, aucune injection vers Dofus, aucun contrôle du client, aucune collecte d'identifiants Ankama et aucun stockage de paquets bruts.

Avant une pull request :

```bash
python3 -m py_compile macos/astrub_companion.py
bash -n macos/install.sh macos/Installer.command macos/Pause.command macos/Reprendre.command macos/Statut.command macos/Desinstaller.command
```
