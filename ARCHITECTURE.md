# Architecture

Sur macOS, `launchd` exécute le collecteur et `tcpdump` lui transmet en mémoire le trafic filtré. Sur Windows, une tâche système lance le même moteur, qui appelle directement Npcap sur les interfaces actives. Dans les deux cas, le filtre est `tcp port 5555` et aucun fichier PCAP n'est créé. Le collecteur reconstruit les flux TCP par numéro de séquence, retire les retransmissions, reconnaît les enveloppes Protobuf `type.ankama.com` puis ignore tout le reste.

Événements HDV pris en charge :

| Usage | Séquence exigée |
|---|---|
| Consultation par lot | `keh`, `kde` ou `kcy` demandant les prix, puis réponse détaillée `kbt`, `jzn` ou `jzs` du même objet |
| Achat par lot | `keh`, `kbm`, confirmation `kgp`, ajout inventaire `iua` |
| Mise en vente par lot | `keh`, `kbz`, puis `kge` |
| Modification | confirmation serveur `kes` contenant objet, prix et quantité |

Le programme n'ouvre aucune connexion vers les serveurs Ankama. Sa seule connexion sortante propre est un POST HTTPS vers l'API Astrub.net.

Les identifiants techniques d'offre utilisés pour corréler localement une vente ou un achat sont supprimés avant la mise en file et ne sont jamais transmis à Astrub.net.

## Minimum des consultations HDV (1.2.2)

Les réponses `jzn`, `kbt` et `jzs` peuvent contenir plusieurs variantes du même équipement.
Le collecteur parcourt toutes les entrées dont l’identifiant correspond à l’objet demandé,
puis retient séparément le plus petit prix strictement positif pour chaque lot ×1, ×10,
×100 et ×1000. Le montant transmis est le prix total du lot, sans division par sa quantité.
Les lots absents ou à zéro ne sont pas transmis. Une réponse tronquée n’est pas publiée.
Depuis Dofus 3.7, `kcy` porte l'identifiant d'objet dans son premier champ et le drapeau
de demande de prix dans le deuxième ; `jzs` porte les variantes dans son premier champ,
l'identifiant d'objet dans le troisième et les prix par lot dans le deuxième champ de
chaque variante. La réponse n'est retenue que si la demande de prix correspondante a été
observée pour le même objet.

Les événements d’achat, de mise en vente et de modification conservent leur fonctionnement
1.2.0 : ils décrivent une transaction, et ne constituent pas un relevé exhaustif du marché.
La déduplication, la file persistante et la reprise des événements rejetés pour `device_id`
sont conservées.

Les sources 1.2.1 reprennent les moteurs des archives versionnées 1.2.0 dont les SHA-256
figurent dans les notes de cette release. Le tag 1.2.0 et les archives sans numéro de version
contenaient encore le moteur ×1 précédent. Les commandes de notification de mise à jour
du dépôt sont également conservées. Les futures archives sont construites depuis le tag
après exécution des tests.
