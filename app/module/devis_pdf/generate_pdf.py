from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import os
from datetime import datetime, timedelta

from app.module.devis_pdf.make_table import make_tableau_devis
from myselfiebooth.settings import PDF_REPERTORY, TITULAIRE_DU_COMPTE_A, IBAN_A, BIC_A, BIC_B, TITULAIRE_DU_COMPTE_B, \
    IBAN_B


def generate_devis_pdf(event):

    # Créez un objet BytesIO pour stocker le PDF en mémoire
    buffer = BytesIO()

    # Créez un objet Canvas pour générer le PDF
    pdf = canvas.Canvas(buffer)

    width, height = A4

    # Dessiner l'image avec la transparence réglée
    pdf.drawImage(os.path.join(PDF_REPERTORY, "img/logo-white.jpg"), 40, 180, 500, 500)

    # Ajouter des images pour les logos
    pdf.drawImage(os.path.join(PDF_REPERTORY, "img/bande.jpg"), 0, 780, 600, 65)
    pdf.drawImage(os.path.join(PDF_REPERTORY, "img/bande-bas.jpg"), 0, 0, 600, 65)

    # ----------------------------------------------------------------------------------------
    # Ajouter des zones de texte pour les en-têtes
    pdf.setFont("Times-Bold", 20)
    pdf.drawString(50, height - 125, "DEVIS n°D" + datetime.now().strftime('%y%m') +str(int(event.id)+27))
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(50, height - 142, "Établi le "+ datetime.now().strftime('%d/%m/%Y'))
    # ----------------------------------------------------------------------------------------
    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.black)
    pdf.drawString(50, height - 180, "MySelfieBooth")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(50, height - 195, "0699733998")
    pdf.drawString(50, height - 210, "contact@myselfiebooth-paris.fr")
    pdf.drawString(50, height - 225, "www.myselfiebooth-paris.fr")
    # ----------------------------------------------------------------------------------------
    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.black)
    nom_prenom_client = str(event.client.prenom) + " " + str(event.client.nom)
    pdf.drawString(330, height - 180, nom_prenom_client)
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    num_client = str(event.client.numero_telephone)
    pdf.drawString(330, height - 195, num_client)
    mail_client = str(event.client.mail)
    pdf.drawString(330, height - 210, mail_client)

    # ----------------------------------------------------------------------------------------

    # Ajouter un tableau pour les articles
    data_tableau_devis, acompte = make_tableau_devis(event)

    table = Table(data_tableau_devis, colWidths=[210, 80, 70, 80, 95])
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Ajout de lignes horizontales après chaque ligne de la table
    for i in range(len(data_tableau_devis)):
        table_style.append(('LINEBELOW', (0, i), (-1, i), 1, colors.grey))

    table.setStyle(TableStyle(table_style))

    # Hauteur de départ pour l'en-tête de la table
    start_y_position = height - 400  # Ajustez ce nombre selon l'emplacement souhaité pour l'en-tête
    # Calculez la hauteur de la table (en supposant que chaque ligne a une hauteur fixe pour simplifier)
    line_height = 20  # Ajustez ceci selon la hauteur de vos lignes
    table_height = len(data_tableau_devis) * line_height
    # Position y pour le bas de la table
    y_position = start_y_position - table_height

    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 30, y_position)

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(447, y_position - 18, "sous-total :")
    pdf.drawString(507, y_position - 18, "100 €")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(375.5, y_position - 33, "Remises supplémentaires :")
    pdf.drawString(505.8, y_position - 33, "-100 €")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(463, y_position - 50, "Total :")
    pdf.drawString(507, y_position - 50, "100 €")

    # ----------------------------------------------------------------------------------------

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(65, height - 635, "Modalité de payement:")
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.darkslategrey)
    # Calcul de la date de J+10
    date_j_plus_10 = datetime.now() + timedelta(days=10)
    pdf.drawString(65, height - 650, "Un acompte de " + acompte + " € est à verser pour confirmer la réservation avant le " + date_j_plus_10.strftime('%d/%m/%Y'))
    pdf.drawString(65, height - 665, "Le reste est à payer au moment de la livraison ou au moins 2 jours avant l'évènement")
    pdf.drawString(65, height - 680, "Vous pouvez payer par virement (RIB à droite), Paylib, Paypal (paypal.me/3dmouvstudio)")

    # ----------------------------------------------------------------------------------------

    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(65, height - 710, "RIB:")
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.darkslategrey)

    # Logique pour déterminer quel RIB utiliser, ici on utilise un flag pour l'exemple
    utiliser_rib_a = True  # ou une condition/fonction qui détermine quel RIB utiliser
    if utiliser_rib_a:
        titulaire = TITULAIRE_DU_COMPTE_A
        iban = IBAN_A
        bic = BIC_A
    else:
        titulaire = TITULAIRE_DU_COMPTE_B
        iban = IBAN_B
        bic = BIC_B

    # Générer le PDF avec les informations sélectionnées
    pdf.drawString(65, height - 725, f"TITULAIRE DU COMPTE : {titulaire}")
    pdf.drawString(65, height - 737, f"IBAN : {iban}")
    pdf.drawString(65, height - 749, f"BIC : {bic}")

    # Finaliser le PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

