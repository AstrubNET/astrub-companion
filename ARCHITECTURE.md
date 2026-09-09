# Architecture

Sur macOS, `launchd` exécute le collecteur et `tcpdump` lui transmet en mémoire le trafic filtré. Sur Windows, une tâche système lance le même moteur, qui appelle directement Npcap sur les interfaces actives. Dans les deux cas, le filtre est `tcp port 5555` et aucun fichier PCAP n'est créé. Le collecteur reconstruit les flux TCP par numéro de séquence, retire les retransmissions, reconnaît les enveloppes Protobuf `type.ankama.com` puis ignore tout le reste.

Événements HDV pris en charge :

| Usage | Séquence exigée |
|---|---|
| Consultation ×1 | `keh(item_id, 1)` puis réponse détaillée `kbt` du même objet |
| Achat ×1 | `keh`, `kbm`, confirmation `kgp`, ajout inventaire `iua` |
| Mise en vente ×1 | `keh`, `kbz`, puis `kge` |
| Modification | confirmation serveur `kes` contenant objet, prix et quantité |

Le programme n'ouvre aucune connexion vers les serveurs Ankama. Sa seule connexion sortante propre est un POST HTTPS vers l'API Astrub.net.

Les identifiants techniques d'offre utilisés pour corréler localement une vente ou un achat sont supprimés avant la mise en file et ne sont jamais transmis à Astrub.net.
