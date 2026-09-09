# Confidentialité

## Données envoyées à Astrub.net

- identifiant numérique de l'objet Dofus ;
- prix unitaire observé ;
- identifiant du serveur choisi ;
- quantité, toujours égale à 1 ;
- type d'observation : consultation, achat, vente ou modification ;
- date de l'observation ;
- UUID aléatoire de l'événement ;
- UUID aléatoire propre à l'installation.

L'UUID d'installation est créé localement. Il n'est dérivé ni du matériel, ni du compte macOS/Windows, ni du compte Ankama. L'API le transforme immédiatement en empreinte SHA-256 avant stockage.

## Données qui ne sont pas collectées

- identifiant ou mot de passe Ankama ;
- pseudo du compte ou du personnage ;
- adresse électronique ;
- adresse MAC ou numéro de série de l'ordinateur ;
- messages du chat ;
- inventaire complet ;
- captures d'écran ;
- fichiers PCAP.

L'adresse IP est nécessairement traitée lors de la connexion HTTPS par Cloudflare et le serveur web, comme pour toute visite d'un site. L'API Companion fournie dans ce dépôt ne l'enregistre pas dans la base applicative. Les journaux techniques de Cloudflare ou de l'hébergeur peuvent néanmoins la traiter selon leur propre configuration et leur durée de conservation.

## Traitement local

Sur macOS, `tcpdump` remet les paquets en mémoire au collecteur. Sur Windows, le collecteur les reçoit directement de Npcap. Les messages non reconnus ou sans rapport avec une opération HDV utile sont abandonnés. Les paquets bruts ne sont jamais écrits sur le disque.

La file SQLite locale ne contient que les contributions structurées qui restent à transmettre et les erreurs mises en quarantaine.
