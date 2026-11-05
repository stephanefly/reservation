# MySelfieBooth — CRM et règles métier (Codex)

Le CRM Django `reservation` est un outil commercial et opérationnel. Préserver les devis, factures, données clients et règles en production. Les instructions de travail réutilisables sont sous `.agents/skills/`.

## Contextes
- Référentiel métier (Notion) : https://app.notion.com/p/40f481b9179581fc8385c0a9cafa0dc3
- Skills Notion : catalogue https://app.notion.com/p/40f481b917958190b16cebb7bad2a1ea ; commercial https://app.notion.com/p/40f481b91795816ba0f5e693de4cdbab ; CRM https://app.notion.com/p/40f481b9179581bd9ac4f353c311eaf9.
- Au démarrage des tâches pertinentes, consulter la skill Notion si elle est accessible, sinon lire la skill locale correspondante. Ne pas croire qu'une skill donne une permission API.
- Documents de code à lire : `docs/catalogue-commercial.md`, `docs/admin-devis-auto.md`, `docs/ux-guidelines-crm.md`, `docs/deploiement-pythonanywhere.md`, `docs/sauvegarde-mysql-pythonanywhere.md`.

## Règles métier minimales
- Photobooth = borne photo ; Miroirbooth = miroir tactile ; 360 = vidéo ; Vogue = studio lumineux. Phonebooth audio et livre d'or vidéo sont différents.
- Entreprises : devis manuel, pas d'acompte demandé, facture globale selon politique ; « RECOMMANDATION » : devis auto interdit. Prix minimum commercial 350 € TTC.
- Les activations automatiques (module global, mode catalogue, éligibilité offre) sont indépendantes. Ne pas activer des envois automatiques ou une migration en modifiant simplement les textes.
- Les nouvelles demandes doivent être conservées. Ne pas envoyer de mails en simulation, ne pas modifier les montants existants, ne pas supposer que le catalogue réécrit les prix PDF.
- Ne jamais révéler settings.yaml ni identifiants ; aucune opération sur base de production sans consigne explicite et sauvegarde vérifiée.
- PR avec tests et diff clair avant fusion. Préférer interface simple, deux blocs maximum quand la tâche l'exige, simulations compréhensibles.
