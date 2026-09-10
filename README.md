# Astrub Companion

Collecteur communautaire et open source de prix HDV pour **Dofus**, disponible sur Windows et macOS.

Astrub Companion observe passivement les échanges réseau déjà produits lorsque le joueur consulte ou utilise un hôtel de vente. Il reconnaît uniquement les informations utiles au prix unitaire et les transmet anonymement à [Astrub.net](https://www.astrub.net/).

> Projet communautaire indépendant, non édité, non approuvé et non affilié à Ankama. Dofus, Ankama et le Monde des Douze appartiennent à leurs propriétaires respectifs.

## Télécharger

Les installateurs se trouvent dans la [dernière version publiée](../../releases/latest) :

- **Windows** : `Astrub-Companion-Windows.zip` ;
- **macOS / MacBook** : `Astrub-Companion-macOS.zip`.

## Fonctionnement

- écoute locale et passive du trafic TCP Dofus sur le port de jeu `5555` ;
- reconnaissance des consultations HDV, achats, mises en vente et modifications de tarif ;
- prise en compte exclusive des offres en quantité ×1 ;
- envoi HTTPS vers Astrub.net avec mise en file locale si Internet est indisponible ;
- aucun compte Astrub et aucun token requis.

## Ce que le programme ne fait pas

- aucun clic, déplacement ou achat automatisé ;
- aucune injection et aucune émission de paquet vers Ankama ;
- aucune lecture des identifiants ou mots de passe Ankama ;
- aucun envoi du pseudo, du personnage, du chat ou de l'inventaire complet ;
- aucun enregistrement de fichier PCAP ;
- aucun code obfusqué.

## Sécurité du compte Dofus

Astrub Companion n'accède jamais au formulaire de connexion, au mot de passe, au jeton de session ou aux cookies Ankama. Il ne lit pas la mémoire de Dofus, ne modifie aucun fichier du jeu et ne se connecte jamais à la place du joueur. Le code publié ne contient donc aucun mécanisme de vol de compte ou de prise de contrôle.

Le filtre de capture est limité au trafic TCP utilisant le port de jeu `5555`. Les paquets passent brièvement en mémoire ; seules les séquences HDV documentées sont interprétées. Tout autre message est abandonné et aucun paquet brut n'est enregistré.

Cette garantie concerne exclusivement le code de ce dépôt officiel. Comme pour tout logiciel, une copie modifiée distribuée ailleurs pourrait se comporter différemment : téléchargez uniquement les releases de `AstrubNET/astrub-companion` et vérifiez le code ou les empreintes publiées.

Le détail précis des champs traités est public dans [PRIVACY.md](PRIVACY.md). Le fonctionnement technique est documenté dans [ARCHITECTURE.md](ARCHITECTURE.md).

## Installation Windows

1. Téléchargez et décompressez `Astrub-Companion-Windows.zip`.
2. Double-cliquez sur `Installer.cmd`.
3. Si Npcap est absent, son installateur officiel signé est téléchargé directement depuis `npcap.com`.
4. Choisissez votre serveur Dofus et validez.

Le service démarre ensuite automatiquement avec Windows. Consultez [la documentation Windows](windows/README.md).

## Installation macOS

1. Téléchargez et décompressez `Astrub-Companion-macOS.zip`.
2. Faites un clic droit sur `Installer.command`, puis **Ouvrir**.
3. Si macOS bloque encore le fichier, ouvrez **Réglages Système > Confidentialité et sécurité**, descendez jusqu'à la section **Sécurité**, puis cliquez sur **Ouvrir quand même** en face de `Installer.command` et confirmez.
4. Choisissez votre serveur Dofus et validez.

Si macOS indique que vous ne disposez pas des privilèges nécessaires, ouvrez Terminal dans le dossier décompressé et exécutez :

```bash
chmod +x *.command *.sh
./Installer.command
```

Le service démarre ensuite automatiquement avec le Mac. Consultez [la documentation macOS](macos/README.md).

## Mises à jour

Astrub Companion vérifie uniquement la dernière release stable publiée sur le dépôt officiel GitHub. Lorsqu'une version plus récente est disponible, une notification native propose d'ouvrir sa page de téléchargement : aucune archive provenant d'un autre domaine n'est utilisée et aucune mise à jour n'est installée silencieusement avec des privilèges administrateur.

- **Windows** : vérification à l'ouverture de session et chaque jour ;
- **macOS** : vérification à l'ouverture de session puis toutes les six heures ;
- une commande **RechercherUneMiseAJour** est également fournie sur les deux plateformes.

## FAQ

Les réponses sur la sécurité, les données envoyées, Npcap, les bannissements et la désinstallation sont réunies dans [FAQ.md](FAQ.md).

## Développement et audit

Le moteur est écrit en Python 3 sans dépendance Python externe. Windows utilise Npcap ; macOS utilise l'outil système `tcpdump`.

```bash
git clone https://github.com/AstrubNET/astrub-companion.git
cd astrub-companion
python3 -m py_compile macos/astrub_companion.py windows/astrub_companion.py
```

Voir [CONTRIBUTING.md](CONTRIBUTING.md) et [SECURITY.md](SECURITY.md).

## Avertissement

L'analyse d'un protocole réseau, même passive, peut être considérée comme contraire aux conditions d'utilisation d'Ankama. Astrub Companion n'automatise aucune action en jeu, mais son utilisation reste sous la responsabilité de chaque utilisateur.

## Limites connues

- seuls les prix de lots ×1 sont transmis ;
- un prix n'est visible que lorsque Dofus envoie le détail de l'objet consulté ou confirme une opération reconnue ;
- ouvrir une catégorie ne fournit pas tous ses prix et le Companion ne parcourt jamais automatiquement les objets ;
- une modification du protocole ou du port par Ankama peut interrompre la détection ;
- Windows nécessite Npcap et macOS nécessite les droits de capture de `tcpdump` ;
- les prix communautaires restent indicatifs et peuvent évoluer après leur observation ;
- aucune garantie de conformité aux conditions d'utilisation d'Ankama n'est donnée.

## Licence

[MIT](LICENSE). Npcap reste un composant séparé soumis à sa propre licence et n'est pas redistribué dans le dépôt.
