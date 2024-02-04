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
    pdf.drawImage(r"C:\Users\s575264\PycharmProjects\reservation\app\static\img\logo.png", 100, 200, 500, 500)

    # Ajouter des zones de texte pour les en-têtes
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, height - 50, "MONIER ÉLECTRICITÉ")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 70, "DEVIS ESTIMATIF")

    # Informations du client
    pdf.drawString(50, height - 120, "Monsieur Lionel TEST")
    pdf.drawString(50, height - 140, "Rue de la Paix")
    pdf.drawString(50, height - 160, "34000 MONTPELLIER")

    # Informations du devis
    pdf.drawString(400, height - 120, "Référence : 1234")
    pdf.drawString(400, height - 140, "Le : 12/04/2013")
    pdf.drawString(400, height - 160, "Objet : Exemple de Devis")

    # Ajouter un tableau pour les articles
    data = [['N°', 'LIBELLÉ', 'U', 'P.U. HT', 'QTÉ', 'TOTAL HT'],
            # Ajoutez ici les lignes de détails de vos articles
           ]

    table = Table(data, colWidths=[50, 180, 50, 80, 50, 100])
    table.setStyle(TableStyle([
                         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                         ('GRID', (0,0), (-1,-1), 1, colors.black),
                     ]))
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 50, height - 400)

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


with open("facture.pdf", "wb") as f:
    f.write(pdf_content)
