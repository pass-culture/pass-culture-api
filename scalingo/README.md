# Scalingo deploy

Première étape, installer la cli scalingo :

curl -O https://cli-dl.scalingo.io/install && bash install


Ajouter votre clé ssh pour effectuer les opérations sur scalingo depuis votre terminal :

`scalingo keys-add [KEY_NAME] [PUBLIC_KEY]`

Si vous souhaitez créer une nouvelle clé :

`ssh-keygen -t rsa -b 4096 -C "your_email@example.com"`


## Création d'un nouvel environnement sur Scalingo :

Utiliser le script `init_new_project.sh`
Example d'appel : pour créer un projet à l'URL api.passculture-dev.beta.gouv.fr avec une base de donnée postgresql de type 1g 
(https://scalingo.com/databases/postgresql) et 2 instances de backend.
La commande déploiera ensuite la branche locale de votre dépôt Github.

`./init_new_project.sh -n pass-culture-api-dev -r dev -d 1g -b 2 -u api.passculture-dev.beta.gouv.fr -j MAILJET_API_SECRET -k MAILJET_API_KEY -e dev`


Ensuite, lancer le script `init_google_env.sh` afin de positionner les variables d'environnements nécessaires à la connexion
au Google Sheet de vérification des utilisateurs.

`./init_google_env.sh -a pass-culture-api-dev -j [JSON_CREDENTIALS]`

avec JSON_CREDENTIALS, les informations nécessaires au format json dans un champ texte.


Si l'environnement que vous souhaitez déployer a besoin de stocker des objets sur un disque OVH, un dernier script devra être lancé `init_bucket_env.sh`.

`./init_bucket_env.sh -a pass-culture-api-dev -u [OPENSTACK_USER] -p [OPENSTACK_PASSWORD] -c storage-pc-dev -t [TENANT_NAME]`



## Restauration d'un backup sur l'un des environnements Scalingo

Première étape, installer les paquets clients de postgresql :

`apt install postgresql-client-9.5`

(Les autres versions postgresql-client > 9.5 devraient fonctionner)

Le script `restore_backup.sh` permet de restaurer sur un environnement Scalingo un dump de base de données postgres.
Le dump peut-être local avec l'option `-b` ou en récupérant un backup de production sur OVH `-o`.
Exemple d'appel du script (avec récupération de la production actuelle):

`./restore_backup.sh -a pass-culture-api-dev -d $SCALINGO_POSTGRESQL_URL_STAGING -p $SCALINGO_PG_PASSWORD_STAGING -u $SCALINGO_PG_USER_STAGING -o`

