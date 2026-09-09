# Déploiement de l'API anonyme

1. Sauvegarder la base et l'ancien `prices.php`.
2. Exécuter `database/migration-anonymous-v1.sql` une seule fois.
3. Déployer `public/api/companion/prices.php` et `servers.php` dans le dossier correspondant du site.
4. Vérifier `https://www.astrub.net/api/companion/servers.php`.
5. Configurer dans Cloudflare une limitation POST sur `/api/companion/prices.php`, par exemple 240 requêtes par minute et par IP, en complément des 200 événements par minute et par installation appliqués par PHP.

L'API ne requiert aucun token. Elle ne stocke pas l'adresse IP dans les tables applicatives. L'UUID d'installation est stocké uniquement sous forme d'empreinte SHA-256.
