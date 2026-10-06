## Compatibilité avec Dofus 3.7

Les consultations HDV utilisent désormais aussi les messages `kcy` et `jzs`. Cette version
reconnaît ces messages et transmet à Astrub.net le prix minimum observé pour chaque lot
×1, ×10, ×100 et ×1000. Les lots absents ou à zéro sont ignorés. Dans la capture de
validation Dofus 3.7, l'objet 13831 remonte à **100 000 kamas** pour le lot ×1.

Les anciens messages HDV restent pris en charge. La collecte demeure passive et les
observations continuent de passer par la file locale avec déduplication.

## Installation

Téléchargez l’archive de votre système, décompressez-la et relancez l’installateur.
Sur macOS, ouvrez le dossier `macos` puis `Installer.command`.
Sur Windows, ouvrez le dossier `windows` puis `Installer.cmd`.

Les tests macOS et Windows couvrent l'objet 13831, le minimum par lot, les lots absents,
les réponses tronquées et la mise en file des prix destinés à l’API.
