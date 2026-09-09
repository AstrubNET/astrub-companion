# Foire aux questions — Astrub Companion

## Astrub Companion est-il gratuit et open source ?

Oui. L'intégralité du code est publiée sous licence MIT. Les installateurs, le moteur de décodage et les scripts de démarrage sont lisibles dans ce dépôt.

## Faut-il un compte Astrub.net ou un token ?

Non. La contribution est anonyme. Un UUID aléatoire est créé localement pour limiter les abus ; il n'est lié ni à votre matériel, ni à votre compte Ankama.

## Quelles données sont envoyées ?

L'identifiant générique de l'objet Dofus, le prix unitaire, le serveur choisi, la quantité ×1, le type d'observation, la date et deux UUID aléatoires. Consultez [PRIVACY.md](PRIVACY.md) pour la liste exhaustive.

## Le programme récupère-t-il mes identifiants ou mon personnage ?

Non. Il ne cherche ni identifiant Ankama, ni mot de passe, pseudo, nom de personnage, chat ou inventaire complet. Les identifiants techniques d'offres employés pour la corrélation locale sont supprimés avant tout envoi.

## Astrub Companion peut-il pirater mon compte Dofus ?

Le code officiel publié ici ne possède aucun mécanisme permettant de voler ou d'utiliser un compte. Il n'accède pas au formulaire de connexion, aux mots de passe, aux cookies, aux jetons de session, à la mémoire du jeu ou aux fichiers de Dofus. Il ne se connecte jamais aux serveurs Ankama de sa propre initiative.

Cette réponse vaut pour les releases officielles de ce dépôt. N'installez pas une copie modifiée provenant d'un site, d'un message privé ou d'un dépôt inconnu.

## Est-ce un bot Dofus ?

Astrub Companion ne clique pas et ne contrôle pas Dofus. Il ne fabrique, ne modifie et n'injecte aucun paquet. Il observe passivement des messages déjà échangés à la suite des actions du joueur.

## Existe-t-il un risque de bannissement ?

Le programme n'automatise aucune action en jeu, mais l'analyse du protocole peut rester contraire aux conditions d'utilisation d'Ankama. Il n'existe donc pas de garantie de risque nul. L'utilisation est laissée à la responsabilité de chacun.

## Pourquoi seuls les prix ×1 sont-ils relevés ?

Astrub.net compare les prix unitaires. Les lots ×10 et ×100 peuvent avoir une tarification différente ; ils sont volontairement ignorés pour éviter de mélanger des offres différentes.

## Le Companion récupère-t-il tous les prix d'une catégorie ?

Non. L'ouverture d'une catégorie transmet surtout une liste d'objets, pas tous leurs tarifs. Un prix est relevé lorsque Dofus reçoit le détail de l'objet effectivement consulté. Le Companion n'effectue aucun parcours automatique.

## Pourquoi Windows demande-t-il Npcap ?

Windows ne fournit pas directement l'équivalent de `tcpdump`. Npcap donne un accès passif aux paquets réseau. Son édition gratuite interdit la redistribution et l'installation silencieuse : Astrub Companion le télécharge donc directement depuis le site officiel, vérifie sa signature puis affiche son assistant.

## macOS refuse d'ouvrir `Installer.command`. Que faire ?

Faites d'abord un clic droit sur `Installer.command`, puis choisissez **Ouvrir**. Si macOS le bloque encore, ouvrez **Réglages Système > Confidentialité et sécurité**, descendez jusqu'à la section **Sécurité**, puis cliquez sur **Ouvrir quand même** et confirmez. Ce bouton apparaît après une première tentative d'ouverture.

Si le message parle de « privilèges d'accès nécessaires », le fichier n'est pas exécutable. Dans Terminal, depuis le dossier décompressé, lancez `chmod +x *.command *.sh`, puis `./Installer.command`. Les archives 1.1.2 et suivantes corrigent automatiquement ce droit.

## Les paquets sont-ils sauvegardés ?

Non. Ils sont filtrés et traités en mémoire. Aucun fichier `.pcap` ou `.pcapng` n'est créé.

## Le programme voit-il tout mon trafic Internet ?

Npcap et `tcpdump` sont des outils de capture généraux, mais Astrub Companion leur applique le filtre `tcp port 5555`. Son moteur ne reconnaît ensuite que quelques messages HDV documentés. Il n'analyse pas la navigation web, les emails ou les autres applications.

## Quelles sont les limites de la détection ?

Seuls les lots ×1 et les événements HDV connus sont pris en charge. L'ouverture d'une catégorie ne donne pas automatiquement tous ses prix. La détection peut cesser de fonctionner si Ankama modifie son protocole, son format de messages ou son port réseau.

## Que se passe-t-il si Astrub.net est indisponible ?

La contribution structurée est conservée dans une petite file SQLite locale puis retentée plus tard. Les paquets bruts ne sont pas conservés.

## Comment arrêter ou désinstaller le programme ?

Chaque archive contient des commandes **Pause**, **Reprendre**, **Statut** et **Désinstaller**. Sous Windows, Npcap est conservé car Wireshark ou d'autres logiciels peuvent l'utiliser.

## Puis-je vérifier ce qui est envoyé à l'API ?

Oui. Recherchez `enqueue_once` et `flush` dans `astrub_companion.py`. Les champs `object_uid` et `offer_id` sont explicitement supprimés avant la mise en file et l'envoi HTTPS.

## Puis-je contribuer au projet ?

Oui. Les rapports de bugs et pull requests sont les bienvenus. Ne publiez jamais de capture réseau contenant des informations privées dans une issue publique.
