from datetime import datetime, timedelta

from app.models import EmailTracking


def complete_mail(event, soup, mail_type):
    # Complétion des champs communs
    soup.find('b', class_='client_nom').string = str(event.client.nom)
    try:
        soup.find('a', class_='date_event').string = str(event.event_details.date_evenement.strftime('%d/%m/%Y'))
    except AttributeError:
        pass

    if 'devis' in mail_type:
        _handle_reduc(event, soup, mail_type)
        _handle_date_butoire(event, soup, mail_type)
        _handle_acompte(event, soup)
        _handle_tracer(event, soup)

    elif mail_type == 'send_media':
        _handle_send_media(event, soup)

    _handle_unsubscribe(event, soup)

    return soup


def _handle_acompte(event, soup):

    if event.client.raison_sociale:
        balise_acompte = soup.find('div', class_='acompte_particulier')
        balise_acompte.extract()
    else:
        balise_acompte = soup.find('div', class_='acompte_entreprise')
        balise_acompte.extract()
        # Gestion des acomptes selon le prix proposé
        acompte = "150 €" if event.prix_proposed >= 1000 else "100 €" if event.prix_proposed >= 600 else "50 €"
        soup.find('b', class_='acompte').string = acompte


def _handle_date_butoire(event, soup, mail_type):
    # Ajouter X jours à la date butoir
    if mail_type == 'devis':
        jours_restant = 8
    if mail_type == 'rappel_devis':
        jours_restant = 6
    if mail_type == 'last_rappel_devis':
        jours_restant = 3
    if mail_type == 'prolongation_devis':
        jours_restant = 5
    if mail_type == 'phonebooth_offert_devis':
        jours_restant = 5
    if mail_type == 'last_chance_devis':
        jours_restant = 5

    date_j_plus_10 = datetime.now() + timedelta(days=jours_restant)
    soup.find('b', class_='date_butoire').string = date_j_plus_10.strftime('%d/%m/%Y')


def _handle_reduc(event, soup, mail_type):

    # Gestion des réductions
    if mail_type == 'phonebooth_offert_devis':
        event.event_option.Phonebooth = True
        event.event_option.Phonebooth_reduc_prix = 50
        event.event_option.save()

    if mail_type == 'last_chance_devis':
        event.reduc_all = event.reduc_all+50
        event.prix_proposed = event.prix_proposed-50
        event.save()
    reduction = event.reduc_product + event.reduc_all + event.event_option.total_reduction()

    if reduction > 0:
        soup.find('a', class_='txt_reduc').string = " et bénéficier de la réduction de "
        soup.find('a', class_='reduc_all').string = f"{reduction}€"
    else:
        soup.find('a', class_='txt_reduc').string = ""
        soup.find('a', class_='reduc_all').string = ""

    if mail_type == 'relance_devis' or mail_type == 'last_chance_devis':
        soup.find('a', class_='reduc_all_title').string = f"-{reduction}€"


def _handle_send_media(event, soup):
    soup.find('b', class_='client_nom').string = str(event.client.nom)
    a_tag = soup.find('a', class_='link_media_shared')
    a_tag['href'] = str(event.event_template.link_media_shared)


def _handle_unsubscribe(event, soup):
    event_token = event.event_token
    unsubscribe_url = f"https://reservation.myselfiebooth-paris.fr/desabonner/{event_token}"
    soup.find('a', class_='mail_desabonnement')['href'] = unsubscribe_url
    soup.find('a', class_='mail_client').string = str(event.client.mail)

def _handle_tracer(event, soup):

    # Enregistrer le tracking en base de données
    email_traced = EmailTracking.objects.create(
        event_traced=event.id,
        status_devis=event.status,
    )

    tracer_link = f"https://reservation.myselfiebooth-paris.fr/track_devis/{email_traced.uuid}"

    # Trouver l'élément avec la classe `traceur_devis`
    soup.find('img', class_='traceur_devis')['src'] = tracer_link
