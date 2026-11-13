# Règles d'écriture dans le CRM MySelfieBooth

## Objectif

Une personne qui ouvre une page pour la première fois doit savoir en quelques secondes :
- ce qu'elle peut faire ;
- où cliquer ;
- ce qui change après l'enregistrement ;
- ce qui ne change pas automatiquement.

## Règles utilisées sur Catalogue et Devis automatiques

1. **Une action principale par écran.** Exemple : « Enregistrer l'offre ».
2. **Titres orientés action.** Exemple : « Tester sans envoyer » plutôt que « Simulation ».
3. **Une seule phrase d'aide sous les champs sensibles.**
4. **Toujours expliquer les conséquences.** Prix publics (Tarifs/Brochure) ≠ calcul du devis PDF ≠ envoi automatique.
5. **Donner un exemple concret** lorsque le champ est difficile (pack = machine + options + quantités).
6. **Réserver les détails techniques aux zones dépliables** plutôt qu'allonger tous les paragraphes.
7. **Messages de confirmation courts**, sans laisser supposer qu'une opération non effectuée a réussi.
8. **Pas de nouveaux interrupteurs silencieux** et ne pas modifier les règles commerciales en même temps qu'une amélioration de texte.
9. **Accessibilité :** labels explicites, erreurs visibles, champs utiles regroupés, disposition adaptée au mobile.
10. **Sécurité :** les changements d'interface n'activent pas les devis automatiques et ne modifient ni base ni tarifs existants.

## Exemples d'aide contextualisée

| Réglage | Explication courte |
|---|---|
| Prix TTC | Machines et packs déjà présents : affiché sur Tarifs et Brochure |
| Option | Prix indicatif ; devis manuel. La visibilité publique et l'image se règlent dans la fiche |
| Éligible aux devis automatiques | Ce choix seul n'envoie aucun e-mail |
| Composition du pack | Exemple : Photobooth + Phonebooth + 100 porte-clés |
| Simuler / tester | Vérifier un devis sans envoi ni modification des montants |

Maintenir ces formulations lors des prochaines évolutions, tout en ajustant le texte au comportement réel du code.
