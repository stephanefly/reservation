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
    # pdf.drawImage(r"C:\Users\FAURE-Stephane\PycharmProjects\myselfiebooth\app\module\devis_pdf\Logo-transparent.png", 50, 120, 550, 550)

    # Ajouter des zones de texte pour les en-têtes
    pdf.setFont("Times-Bold", 22)
    pdf.drawString(50, height - 130, "DEVIS n°...")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 150, "Etabli le XX/XX/XX")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(80, height - 190, "MySelfieBooth")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(80, height - 210, "0699733998")
    pdf.drawString(80, height - 230, "contact@myselfiebooth-paris.fr")
    pdf.drawString(80, height - 250, "www.myselfiebooth-paris.fr")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(350, height - 190, "Client Nom")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(350, height - 210, "0699733998")
    pdf.drawString(350, height - 230, "contact@myselfiebooth-paris.fr")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 300, "Location de PHOTOBOOTH - MIROIRBOOTH - 360BOOTH")
    pdf.drawString(50, height - 320, "Créateur de souvenir !")


    # Ajouter un tableau pour les articles
    data = [['Description', 'Prix unitaire HT', 'QTÉ', 'TOTAL HT'],
            # Ajoutez ici les lignes de détails de vos articles
           ]

    table = Table(data, colWidths=[260, 110, 60, 110])
    table.setStyle(TableStyle([
                         ('BACKGROUND', (0, 0), (-1, 0), colors.black),
                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                         ('GRID', (0,0), (-1,-1), 1, colors.gold),
                     ]))
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 30, height - 360)

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, height - 500, "TOTAL HT :")
    pdf.drawString(500, height - 500, "$0.00")

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 650, "NOTE:")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, height - 670, "Un acompte de 100 euros est à verser pour confirmer la réservation,")
    pdf.drawString(50, height - 685, "avant le 30/10/2022.")
    pdf.drawString(50, height - 705, "Le reste est à payer au moment de la livraison ou au moins 2 jours ")
    pdf.drawString(50, height - 720, "avant l'évènement par virement.")
    pdf.drawString(50, height - 740, "Vous pouvez payer par virement (Info du RIB dans le devis), Paylib,")
    pdf.drawString(50, height - 755, "Paypal (paypal.me/3dmouvstudio) ou Lydia.")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(390, height - 680, "RIB:")
    pdf.setFont("Helvetica", 8)
    pdf.drawString(390, height - 700, "TITULAIRE DU COMPTE : M STEPHANE FAURE")
    pdf.drawString(390, height - 715, "IBAN : FR58 3000 2069 5100 0000 6909 N52")
    pdf.drawString(390, height - 730, "BIC : CRLYFRPP")


    # Finaliser le PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

# Sauvegarder le PDF dans un fichier
pdf_content = generate_devis_pdf()


with open(r"C:\Users\s575264\PycharmProjects\reservation\app\module\devis_pdf\facture2.pdf", "wb") as f:
    f.write(pdf_content)
