# Sécurité

Merci de ne pas publier une vulnérabilité contenant des données personnelles dans une issue publique. Utilisez l'adresse de sécurité indiquée sur Astrub.net.

L'API doit rester derrière HTTPS. Elle valide strictement les champs, les objets, les serveurs, la quantité et les dates. Un rate limit Cloudflare par adresse IP doit compléter la limite applicative par installation, car un UUID local n'est pas un mécanisme d'authentification.

Ne publiez jamais un fichier `config.json` réel ou une base `queue.sqlite3` dans une issue GitHub.
