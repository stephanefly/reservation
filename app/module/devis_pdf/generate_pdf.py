from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

def generate_devis_pdf():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Ajouter des images pour les logos
    pdf.drawImage(r"C:\Users\s575264\PycharmProjects\reservation\app\module\devis_pdf\bande.jpg", 0, 780, 600, 65)
    pdf.drawImage(r"C:\Users\s575264\PycharmProjects\reservation\app\module\devis_pdf\bande-bas.jpg", 0, 0, 600, 65)
    # pdf.drawImage(r"C:\Users\s575264\PycharmProjects\reservation\app\module\devis_pdf\Logo-transparent.png", 50, 120, 550, 550)

    # Ajouter des zones de texte pour les en-têtes
    pdf.setFont("Times-Bold", 22)
    pdf.drawString(50, height - 125, "DEVIS n°...")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(50, height - 145, "Etabli le XX/XX/XX")

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
    pdf.drawString(330, height - 190, "Client Nom")
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(330, height - 205, "0699733998")
    pdf.drawString(330, height - 220, "contact@myselfiebooth-paris.fr")

    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(colors.black)
    pdf.drawString(50, height - 280, "Location de PHOTOBOOTH - MIROIRBOOTH - 360BOOTH")

    # Ajouter un tableau pour les articles
    data = [['Description', 'Prix unitaire', 'QTÉ', 'Réduction', 'TOTAL'],
            ['Photobooth Tirage Illimtés 5h', '450€', '1', "50€",'450€'],
            ['Livraison - Installation \n 18/03/2024 \n 77000 Mareuil-les-Meaux ', '0€', '1', "",'0€'],
            ['Personnalisation', '0€', '1', "",'0€'],
            ['Galerie Web', '0€', '1',"", '0€'],
           ]

    table = Table(data, colWidths=[210, 80, 70, 80, 110])
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Alternance de la couleur de fond pour une ligne sur deux, à partir de la deuxième ligne de données
    for i in range(1, len(data), 2):
        table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lightgoldenrodyellow))
        table_style.append(('BACKGROUND', (0, i+1), (-1, i+1), colors.ghostwhite))

    # Ajout de lignes horizontales après chaque ligne de la table
    for i in range(len(data)):
        table_style.append(('LINEBELOW', (0, i), (-1, i), 1, colors.grey))

    table.setStyle(TableStyle(table_style))

    table.wrapOn(pdf, width, height)
    print(len(data))
    regul_height = height - (380 + len(data)*20)
    print(regul_height)
    table.drawOn(pdf, 30, regul_height)

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(455, height - 515, "TOTAL :")
    pdf.drawString(515, height - 515, "400€")

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(65, height - 635, "Modalité de payement:")
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(65, height - 650, "Un acompte de 100 euros est à verser pour confirmer la réservation avant le 30/10/2022.")
    pdf.drawString(65, height - 665, "Le reste est à payer au moment de la livraison ou au moins 2 jours avant l'évènement")
    pdf.drawString(65, height - 680, "Vous pouvez payer par virement (RIB à droite), Paylib, Paypal (paypal.me/3dmouvstudio)")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(65, height - 710, "RIB:")
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.darkslategrey)
    pdf.drawString(65, height - 725, "TITULAIRE DU COMPTE : M STEPHANE FAURE")
    pdf.drawString(65, height - 740, "IBAN : FR58 3000 2069 5100 0000 6909 N52")
    pdf.drawString(65, height - 755, "BIC : CRLYFRPP")


    # Finaliser le PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

# Sauvegarder le PDF dans un fichier
pdf_content = generate_devis_pdf()


with open(r"C:\Users\s575264\PycharmProjects\reservation\app\module\devis_pdf\facture3.pdf", "wb") as f:
    f.write(pdf_content)
