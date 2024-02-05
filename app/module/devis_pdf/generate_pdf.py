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
    pdf.drawImage(r"C:\Users\FAURE-Stephane\PycharmProjects\myselfiebooth\app\module\devis_pdf\bande.jpg", 0, 770, 600, 65)
    pdf.drawImage(r"C:\Users\FAURE-Stephane\PycharmProjects\myselfiebooth\app\module\devis_pdf\bande-bas.jpg", 0, 0, 600, 65)
    # pdf.drawImage(r"C:\Users\FAURE-Stephane\PycharmProjects\myselfiebooth\app\module\devis_pdf\Logo-transparent.png", 50, 120, 550, 550)

    # Ajouter des zones de texte pour les en-têtes
    pdf.setFont("Times-Bold", 22)
    pdf.drawString(50, height - 130, "DEVIS n°...")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(80, height - 180, "MySelfieBooth")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(80, height - 200, "0699733998")
    pdf.drawString(80, height - 220, "contact@myselfiebooth-paris.fr")
    pdf.drawString(80, height - 240, "www.myselfiebooth-paris.fr")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(350, height - 180, "Client Nom")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(350, height - 200, "0699733998")
    pdf.drawString(350, height - 220, "contact@myselfiebooth-paris.fr")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 290, "Location de PHOTOBOOTH - MIROIRBOOTH - 360BOOTH")
    pdf.drawString(50, height - 310, "Créateur de souvenir !")


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
    table.drawOn(pdf, 30, height - 350)

    # Ajouter les totaux et les conditions
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, height - 500, "TOTAL HT :")
    pdf.drawString(500, height - 500, "$0.00")

    # Finaliser le PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

# Sauvegarder le PDF dans un fichier
pdf_content = generate_devis_pdf()


with open("facture2.pdf", "wb") as f:
    f.write(pdf_content)
