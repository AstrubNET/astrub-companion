# Contribuer

Les correctifs, tests et audits de confidentialité sont bienvenus. Toute modification doit conserver les principes suivants : écoute passive uniquement, aucune injection vers Dofus, aucun contrôle du client, aucune collecte d'identifiants Ankama et aucun stockage de paquets bruts.

Avant une pull request :

```bash
python3 -m py_compile macos/astrub_companion.py
bash -n macos/install.sh macos/Installer.command macos/Pause.command macos/Reprendre.command macos/Statut.command macos/Desinstaller.command
```

Pour publier une version, mettre à jour les versions des installateurs et moteurs,
`RELEASE_NOTES.md` et `VERSION` dans le même commit sur `main`. La modification
de `VERSION` déclenche les tests, la construction des deux archives puis la création
du tag et de la release sur le commit testé.
