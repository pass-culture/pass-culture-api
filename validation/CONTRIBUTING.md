# Package `validation`
Les modules de ce package contiennent des fonctions **pures**, c'est à dire qui offrent une transparence réferentielle
et qui sont sans effets de bord. Elles ont pour but de garantir la cohérence des données reçues en entrée des routes d'API ;
c'est à dire de permettre aux fonctions de _routing_ de décider si un _request body_ ou des _URL query parameters_ sont utilisables.

## Do
Ces fonctions doivent contenir : des vérifications d'intégrité des données passées en paramètre et des éventuelles levées
d'exceptions pour signaler un problème.

Par exemple :
```python
def check_event_occurrence_offerer_exists(offerer):
    if offerer is None:
        api_errors = ApiErrors()
        api_errors.addError('eventOccurrenceId', 'l\'offreur associé à cet évènement est inconnu')
        raise api_errors
```

## Don't
Ces fonctions ne doivent pas contenir : des règles de gestion, des _queries_ vers la base de données ou des appels à des
web services.

## Testing
Ces fonctions sont testées de manière unitaire et ne nécessitent ni _mocking_, ni instanciation de la base de donnée
ou d'un contexte Flask. Ces tests doivent être extrêmement rapides à l'exécution et sont généralement un excellent terrain
d'apprentissage pour le Test Driven Development (TDD).

Ils ont pour objectif de :
* lister les comportements et responsabilités d'une fonction
* lister les exceptions relatives à la cohérence des données
* donner des exemples d'exécution d'une fonction

Par exemple :
```python
def test_check_valid_signup_raises_api_error_if_not_contact_ok():
    # Given
    mocked_request = Mock()
    mocked_request.json = {'password': '87YHJKS*nqde', 'email': 'test@email.com'}

    # When
    with pytest.raises(ApiErrors) as errors:
        check_valid_signup(mocked_request)

    # Then
    assert errors.value.errors['contact_ok'] == ['Vous devez obligatoirement cocher cette case.']
```
