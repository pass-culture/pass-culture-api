# Package `local_providers`

Un provider est un fournisseur de données extérieur au Pass Culture.
Il peut être appelé via une interface local_provider pour ajouter des stocks, des products, des offers ou autre à la base de données, liées à une venue via le venue_provider.

Qu'est ce qu'un local_provider ?
C'est un composant intermédiaire permettant de faire la liaison entre une venue et un provider.

La récupération des données (stock, products, offers, etc.) se fait par des /connectors (API, ftp, etc.) puis sont enregistrées, après traitement, dans notre base de données.


## Créer un nouveau local provider, par exemple, Allociné

Pour récupérer par exemple les stocks via le provider Tite Live pour une venue.
Créer une nouvelle classe qui hérite de Class LocalProvider(Iterator)`

 ```python
 class TiteLiveStocks(LocalProvider):
  def __next__(self)
 ```

### Comment le jouer au quotidien ?
C'est la méthode `updateObjects()` qui initie le processus de récupération, traitement et enregistrement des données :
- via l'interface pro, lorsque l'user synchronise pour la première fois ses données
- via un cron qui vérifie chaque jour `/api/scripts/update_providables.py` qiu va utiliser `do_update()`


### Datas
La récupération des données se fait dans le domaine `/domain/allocine.py` qui va utiliser un connector `connectors/api_allocine` pour faire un appel à l'api ou autre pour récupérer les données à traiter.

### Iteration

Une fois ces données récupérées, on itère dessus via le `__next__`

On créé un create_providable_info
`def __next__(self) -> List[ProvidableInfo]:

  `for providable_infos in self:`
 appelle le __next__

 Deux options, créer ou mettre à jour via les fonctions héritées de /local_providers/local_provider`
 :
 - def _create_object()
 - def _handle_update()


 `Create_providable_info` 
 - produit(s)
 - offre(s)

### Sauvegarde

Tous les 1000 objet on appelle `save_chunk` (CHUNK_MAX_SIZE)

 - /models
 
 Cas particulier de Tite Live
 - référentiel de données
 - stock : venue Provider qui utilise le provider tite live