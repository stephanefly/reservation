from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

def generate_devis_pdf():

    # Créez un objet BytesIO pour stocker le PDF en mémoire
    buffer = BytesIO()

    # Créez un objet Canvas pour générer le PDF
    pdf = canvas.Canvas(buffer)

    width, height = A4

    # Dessiner l'image avec la transparence réglée
    pdf.drawImage(r"\app\module\devis_pdf\logo-white.jpg", 40, 180, 500, 500)

    # Ajouter des images pour les logos
    pdf.drawImage(r"app\module\devis_pdf\bande.jpg", 0, 780, 600, 65)
    pdf.drawImage(r"app\module\devis_pdf\bande-bas.jpg", 0, 0, 600, 65)


    # Ajouter des zones de texte pour les en-têtes
    pdf.setFont("Times-Bold", 22)
    pdf.drawString(50, height - 125, "DEVIS n°XXX")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(50, height - 145, "Établi le XXX/XXX/XXX")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.black)
    pdf.drawString(50, height - 190, "MySelfieBooth")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(50, height - 205, "0699733998")
    pdf.drawString(50, height - 220, "contact@myselfiebooth-paris.fr")
    pdf.drawString(50, height - 235, "www.myselfiebooth-paris.fr")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.black)
    pdf.drawString(330, height - 190, "XXX XXX")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(330, height - 205, "06XXX")
    pdf.drawString(330, height - 220, "XXX@XXX.fr")

    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)
    pdf.drawString(50, height - 270 , "Location de PHOTOBOOTH - MIROIRBOOTH - 360BOOTH")
    # ----------------------------------------------------------------------------------------

    # Ajouter un tableau pour les articles
    data = [['Description', 'Prix unitaire', 'Quantité', 'Réduction', 'Total'],
            ['XXX XXX', 'XXX', '1', "XXX€",'XXX€'],
            ['Livraison - Installation \n XXX/XXX/XXX \n 77XXXXXX XXX ', '0€', '1', "",'0€'],
            ['Personnalisation', '0€', '1', "",'0€'],
            ['Galerie Web', '0€', '1',"", '0€'],
            ]

    table = Table(data, colWidths=[210, 80, 70, 80, 100])
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Ajout de lignes horizontales après chaque ligne de la table
    for i in range(len(data)):
        table_style.append(('LINEBELOW', (0, i), (-1, i), 1, colors.grey))

    table.setStyle(TableStyle(table_style))

    # Hauteur de départ pour l'en-tête de la table
    start_y_position = height - 400  # Ajustez ce nombre selon l'emplacement souhaité pour l'en-tête
    # Calculez la hauteur de la table (en supposant que chaque ligne a une hauteur fixe pour simplifier)
    line_height = 20  # Ajustez ceci selon la hauteur de vos lignes
    table_height = len(data) * line_height
    # Position y pour le bas de la table
    y_position = start_y_position - table_height

    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 30, y_position)

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(455, y_position - 25, "TOTAL :")
    pdf.drawString(510, y_position - 25, "XXX€")

    # ----------------------------------------------------------------------------------------

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(65, height - 625, "Modalité de payement:")
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(65, height - 640, "Un acompte de XXX euros est à verser pour confirmer la réservation avant le XX/XX/XXXX.")
    pdf.drawString(65, height - 654, "Le reste est à payer au moment de la livraison ou au moins 2 jours avant l'évènement")
    pdf.drawString(65, height - 668, "Vous pouvez payer par virement (RIB à droite), Paylib, Paypal (paypal.me/3dmouvstudio)")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(65, height - 700, "RIB:")
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(65, height - 715, "TITULAIRE DU COMPTE : M XXXX XXXXX")
    pdf.drawString(65, height - 727, "IBAN : XXXXXXXXXXXXXXX")
    pdf.drawString(65, height - 739, "BIC : XXXXXXXXX")


    # Finaliser le PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

# # Sauvegarder le PDF dans un fichier
# pdf_content = generate_devis_pdf()
#
#
# with open(r"facture3.pdf", "wb") as f:
#     f.write(pdf_content)
