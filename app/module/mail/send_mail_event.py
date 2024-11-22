import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.application import MIMEApplication
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from django.utils.timezone import now

from app.models import Event
from app.module.data_bdd.post_form import make_num_devis
from app.module.devis_pdf.generate_pdf import generate_pdf_devis
from myselfiebooth.settings import MP, MAIL_MYSELFIEBOOTH, MAIL_TEMPLATE_REPOSITORY, MAIL_COPIE, MAIL_BCC

def send_mail_event(event, mail_type):
    # Configuration du serveur SMTP
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)
    server.login(MAIL_MYSELFIEBOOTH, MP)

    # Définir les sujets et templates en fonction du type de mail
    if mail_type == 'validation':
        subject = "📸 Votre prestation est réservée : préparez-vous à vous éclater ! ✨"
        template_name = "mail_validation.html"
    elif mail_type == 'relance_espace_client':
        subject = "📸 Informations manquantes pour votre événement ✨"
        template_name = "mail_relance_espace_client.html"
    elif mail_type == 'relance_avis':
        subject = "📸 Votre avis compte ! ✨"
        template_name = "mail_relance_avis.html"
        event.client.nb_relance_avis = event.client.nb_relance_avis + 1
        event.client.save()
    elif mail_type == 'relance_devis':
        subject = "📸 Nous avons pensé à vous ! 📅✨"
        template_name = "mail_relance_devis.html"
        event.client.nb_relance_devis = event.client.nb_relance_devis + 1
        event.client.save()
    elif mail_type == 'relance_devis_black_friday':
        subject = "📸 Black Friday : -50€ supplémentaire ! ✨"
        template_name = "mail_relance_devis_black_friday.html"
        event.client.nb_relance_devis = event.client.nb_relance_devis + 1
        event.client.save()
        event.reduc_all = event.reduc_all + 50
        event.prix_proposed = event.prix_proposed - 50
        event.save()
    elif mail_type == 'devis':
        subject = "📸 Votre devis - " + str(event.client.nom) + " ✨"
        template_name = "mail_devis.html"
    else:
        raise ValueError("Type de mail non reconnu.")

    # Configuration de l'email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr(("MySelfieBooth", MAIL_MYSELFIEBOOTH))
    msg['Cc'] = MAIL_COPIE
    msg['To'] = event.client.mail

    # Lecture du template HTML
    template_path = os.path.join(MAIL_TEMPLATE_REPOSITORY, template_name)
    with open(template_path, 'r', encoding='utf-8') as fichier_html:
        html_message = fichier_html.read()

    # Compléter le contenu du mail
    soup = BeautifulSoup(html_message, 'html.parser')
    soup_completed = complete_mail(event, soup, mail_type)

    # Attacher le contenu HTML à l'e-mail
    msg.attach(MIMEText(soup_completed.prettify(), 'html'))

    # Si c'est un devis, générer et attacher le PDF
    if mail_type == 'devis' or mail_type == 'relance_devis' or mail_type == 'relance_devis_black_friday':
        increment_num_devis(event)
        buffer = generate_pdf_devis(event)

        # Attacher le PDF
        pdf_name = 'Devis-' + str(event.client.nom) + ".pdf"
        buffer.seek(0)  # Réinitialisez le pointeur si nécessaire
        part = MIMEApplication(buffer.read(), Name=pdf_name)
        part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
        msg.attach(part)

    # Envoi de l'e-mail
    server.sendmail(MAIL_MYSELFIEBOOTH, [msg['To']] + [MAIL_BCC], msg.as_string())
    server.quit()  # Toujours fermer la connexion au serveur

    return True

def complete_mail(event, soup, mail_type):
    # Complétion des champs communs
    soup.find('b', class_='client_nom').string = str(event.client.nom)
    soup.find('a', class_='date_event').string = str(event.event_details.date_evenement.strftime('%d/%m/%Y'))

    # Gestion des ajouts spécifiques selon le type de mail
    if mail_type == 'validation':
        selected_booths = event.event_product.get_selected_booths()
        prestation_tag = soup.find('b', class_='prestation')
        if prestation_tag:
            prestation_tag.string = selected_booths
    elif mail_type == 'devis' or mail_type == 'relance_devis' or mail_type == 'relance_devis_black_friday':

        # Ajouter 10 jours à la date butoir
        date_j_plus_10 = datetime.now() + timedelta(days=8)
        soup.find('b', class_='date_butoire').string = date_j_plus_10.strftime('%d/%m/%Y')

        # Gestion des acomptes selon le prix proposé
        if event.prix_proposed >= 1000:
            soup.find('b', class_='acompte').string = "150 €"
        elif event.prix_proposed >= 600:
            soup.find('b', class_='acompte').string = "100 €"
        else:
            soup.find('b', class_='acompte').string = "50 €"

        # Gestion des réductions
        reduction = event.reduc_product if event.reduc_all == 0 else event.reduc_all
        if reduction > 0 :
            soup.find('a', class_='txt_reduc').string = " et bénéficier de la reduction de "
            soup.find('a', class_='reduc_all').string = str(reduction) + "€"
        else:
            soup.find('a', class_='txt_reduc').string = ""
            soup.find('a', class_='reduc_all').string = ""
        if mail_type == 'relance_devis':
            soup.find('a', class_='mail_client').string = str(event.client.mail)
            soup.find('a', class_='reduc_all_title').string = "-"+str(reduction) + "€"
            event.status = 'Resended'
            event.save()
            # Créez la variable `unsubscribe_url`
            unsubscribe_url = f"https://reservation.myselfiebooth-paris.fr/desabonner/{event.id}"
            unsubscribe_link = soup.find('a', text="Se désabonner")
            unsubscribe_link['href'] = unsubscribe_url

    return soup

def increment_num_devis(event):
    if event.num_devis:
        # Extraire le préfixe (date + id) et le chiffre à incrémenter
        prefix = event.num_devis[:-1]  # Tout sauf le dernier caractère
        last_digit = event.num_devis[-1:]  # Dernier caractère

        # Vérifier si on doit augmenter la partie numérique à cause d'un '9'
        if last_digit == '9':
            # Trouver la fin de l'identifiant et le début du chiffre à incrémenter
            start_of_increment = len(event.num_devis) - len(event.id) - 1  # Position de départ du chiffre à incrémenter
            prefix = event.num_devis[:start_of_increment]
            number_part = event.num_devis[start_of_increment:]

            # Convertir en nombre et incrémenter
            incremented_number = int(number_part) + 1
            event.num_devis = prefix + str(incremented_number)
        else:
            # Simplement incrémenter le dernier chiffre s'il ne s'agit pas d'un '9'
            incremented_digit = int(last_digit) + 1
            event.num_devis = prefix + str(incremented_digit)
    else:
        make_num_devis(event)
        increment_num_devis(event)

    event.save()

def relance_all_devis_client_black_friday():
    event = Event.objects.filter(
        signer_at__isnull=True,
        client__raison_sociale=False,
        client__autorisation_mail=True,
        client__nb_relance_devis=0,  # Correction ici
        date_evenement__gte=now()  # Filtre pour les événements à venir
    ).order_by('-prix_proposed').first()
    if event:  # Vérifie qu'un événement existe
        send_mail_event(event, 'relance_devis_black_friday')


