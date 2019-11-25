# LOCAL PROVIDER

Qu'est ce qu'un local provider ? C'est un fournisseur de données extérieur au Pass Culture.
Celles ci sont récupérées via plusieurs types d'interface (API, ftp, etc.)
 puis sont enregistrées dans notre base de données.

## Créer un nouveau local provider, par exemple, Allociné

Pour récupérer par exemple les stocks via le provider Tite Live.
Créer une nouvelle classe qui hérite de Class LocalProvider(Iterator)`

 ```python
 class TiteLiveStocks(LocalProvider):
  def __next__(self)
  ```
  
### Datas 
La récupération des données se fait dans le domaine `/domain/allocine.py` qui va utiliser un connector `connectors/api_allocine` pour faire un appel à l'api ou autre pour récupérer les données à traiter.
 
### Iteration

Une fois ces données récupérées, on itère dessus via le `__next__

On créé un create_providable_info

`def __next__(self) -> List[ProvidableInfo]:

  `for providable_infos in self:`
 appelle le __next__
 
 Deux options, créer ou mettre à jour via les fonctions héritées de /local_providers/local_provider`
 :
 - def create_object()
 - def handle_update()
 
 
 `Create_providable_info` génère des objets vides
 - produit(s)
 - offre(s)
 
### Sauvegarde
  
Tous les 1000 objet on appelle `save_chunk` (CHUNK_MAX_SIZE)

 - /models


