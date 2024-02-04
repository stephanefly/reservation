
def generate_devis_pdf(pdf):
    # Titre de la facture
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "FACTURE")

    # Informations du client
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 700, "Client : Nom du Client")
    pdf.drawString(50, 680, "Date : date")
    pdf.drawString(50, 660, "Numéro de Facture : num devis")

    # Tableau des articles
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 620, "Description")
    pdf.drawString(250, 620, "Quantité")
    pdf.drawString(350, 620, "Prix unitaire")
    pdf.drawString(450, 620, "Total")

    y_position = 600
    # Total de la facture
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(350, y_position - 20, "Montant Total :")
    pdf.drawString(450, y_position - 20, f"$0")

    # Terminez le PDF
    pdf.showPage()
    pdf.save()

    return pdf