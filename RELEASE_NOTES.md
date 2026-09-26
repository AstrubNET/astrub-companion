## Prix minimum par lot

Les consultations HDV prennent désormais le prix minimum parmi toutes les variantes
d’un objet, séparément pour les lots ×1, ×10, ×100 et ×1000. Les lots absents ou à zéro
ne sont pas envoyés. Pour l’équipement 8215 de la capture de validation, le prix transmis
est de **180 kamas**, au lieu des 2 499 kamas de la première variante.

Les fonctions des moteurs publiés dans les archives versionnées 1.2.0 sont conservées :
collecte passive, quatre lots, file locale, déduplication et reprise des contributions.
Les sources et les archives sont désormais synchronisées. Les événements de transaction
conservent leurs montants constatés ; cette correction concerne les consultations HDV.

## Installation

Téléchargez l’archive de votre système, décompressez-la et relancez l’installateur.
Sur macOS, ouvrez le dossier `macos` puis `Installer.command`.
Sur Windows, ouvrez le dossier `windows` puis `Installer.cmd`.

Les tests macOS et Windows couvrent les variantes, chaque lot, les lots absents,
les réponses tronquées et la mise en file des prix destinés à l’API.
