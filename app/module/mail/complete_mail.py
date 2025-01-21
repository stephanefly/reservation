from datetime import datetime, timedelta


def complete_mail(event, soup, mail_type):
    # Complétion des champs communs
    soup.find('b', class_='client_nom').string = str(event.client.nom)
    try:
        soup.find('a', class_='date_event').string = str(event.event_details.date_evenement.strftime('%d/%m/%Y'))
    except AttributeError:
        pass

    # Gestion des ajouts spécifiques selon le type de mail
    if mail_type == 'validation':
        selected_booths = event.event_product.get_selected_booths()
        prestation_tag = soup.find('b', class_='prestation')
        if prestation_tag:
            prestation_tag.string = selected_booths

    elif mail_type in ['devis', 'relance_devis', 'last_chance_devis']:
        _handle_devis(event, soup, mail_type)

    elif mail_type == 'send_media':
        _handle_send_media(event, soup)

    if mail_type in ['devis', 'relance_devis', 'one_shoot', 'last_chance_devis']:
        _handle_unsubscribe(event, soup)

    return soup


def _handle_devis(event, soup, mail_type):
    # Ajouter 10 jours à la date butoir
    date_j_plus_10 = datetime.now() + timedelta(days=8)
    soup.find('b', class_='date_butoire').string = date_j_plus_10.strftime('%d/%m/%Y')

    # Gestion des acomptes selon le prix proposé
    acompte = "150 €" if event.prix_proposed >= 1000 else "100 €" if event.prix_proposed >= 600 else "50 €"
    soup.find('b', class_='acompte').string = acompte

    # Gestion des réductions
    reduction = event.reduc_product if event.reduc_all == 0 else event.reduc_all
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
