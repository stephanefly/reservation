"""Lancer un parcours commercial dans Chromium avec base et mails de test."""
import json
import os
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from email import policy
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch
from wsgiref.simple_server import make_server

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

RESULTS = Path("test-results/quote-flow")
MESSAGES = []


def load_event():
    # Playwright utilise une boucle asyncio : lire Django dans un autre thread.
    def query():
        from app.models import Event
        from django.db import connections
        try:
            return Event.objects.select_related("event_option").get()
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(query).result()


class CapturedSMTP:
    """Capturer le mail construit par le véritable code, sans ouvrir de connexion."""
    def __init__(self, *args, **kwargs):
        pass

    def login(self, username, password):
        assert username == "crm@example.invalid"
        assert password == "not-a-production-password"

    def sendmail(self, sender, recipients, message):
        assert sender == "crm@example.invalid"
        assert set(recipients) == {"client@example.invalid", "archive@example.invalid"}
        MESSAGES.append(message.encode("utf-8"))
        return {}

    def quit(self):
        pass


def check_received_mail(expected_total, expected_deposit, expected_quantity, expected_discount):
    message = BytesParser(policy=policy.default).parsebytes(MESSAGES[-1])
    assert message["To"] == "client@example.invalid"
    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    attachment = attachments[0]
    assert attachment.get_content_type() == "application/pdf"
    pdf_bytes = attachment.get_payload(decode=True)
    reader = PdfReader(BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert f"Total :\n{expected_total} €" in text, text
    assert f"Un acompte de {expected_deposit} €" in text, text
    html = BeautifulSoup(message.get_body(preferencelist=("html",)).get_content(), "html.parser")
    assert html.select_one("b.acompte").get_text(strip=True) == f"{expected_deposit} €"
    if expected_quantity:
        option = load_event().event_option
        unit_price = option.panneaux_forfait / expected_quantity
        from app.module.devis_pdf.make_table import format_prix
        expected_line = [
            "Panneau XXL", format_prix(unit_price), str(expected_quantity),
            format_prix(expected_discount) if expected_discount else "",
            format_prix(option.panneaux_forfait - expected_discount),
        ]
        assert "\n".join(item for item in expected_line if item) in text, text
    else:
        assert "Panneau XXL" not in text
    stem = f"devis-{expected_total}"
    (RESULTS / f"{stem}.pdf").write_bytes(pdf_bytes)
    (RESULTS / f"{stem}.eml").write_bytes(MESSAGES[-1])
    return text


def run_browser(base_url):
    from django.db import close_old_connections

    with sync_playwright() as playwright:
        executable = os.environ.get("CRM_E2E_BROWSER_EXECUTABLE")
        browser = playwright.chromium.launch(
            executable_path=executable,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.set_default_timeout(12000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(
            "**/*",
            lambda route: route.continue_() if route.request.url.startswith(base_url + "/")
            else route.abort(),
        )
        try:
            assert page.goto(base_url + "/").ok
            page.locator('.selectable-image[data-value="Photobooth"]').click()
            page.locator("#nextStep").click()
            page.locator("#nextStep").click()
            page.locator(".panneaux-option img").scroll_into_view_if_needed()
            page.wait_for_function(
                "document.querySelector('.panneaux-option img').naturalWidth > 0"
            )
            assert not page.locator("#avec_panneaux").is_checked()
            for quantity, price in {1: 150, 2: 300, 3: 350, 4: 400, 5: 450, 6: 500}.items():
                page.locator(f'.panneau-choice[data-quantite="{quantity}"]').click()
                assert page.locator("#panneaux_xxl").input_value() == str(quantity)
                assert f"{price} €" in page.locator(".panneaux-selection").inner_text()
            page.locator('.panneau-choice[data-quantite="0"]').click()
            assert "Panneau XXL" not in page.locator("#summaryOptions").inner_text()
            page.locator(".panneaux-toggle").click()
            assert page.locator("#panneaux_xxl").input_value() == "4"
            page.screenshot(path=str(RESULTS / "option-client.png"))
            page.locator("#nextStep").click()
            page.locator("#nextStep").click()
            fields = {
                "nom": "Essai", "prenom": "Camille", "mail": "client@example.invalid",
                "numero_telephone": "0100000000",
                "date_evenement": str(date.today() + timedelta(days=60)),
                "adresse_evenement": "1 rue du Test", "ville_evenement": "Paris",
                "code_postal_evenement": "75000",
            }
            for name, value in fields.items():
                page.locator("#id_" + name).fill(value)
            page.locator("#submitStep").click()
            page.locator("#btn-confirm").wait_for()
            assert "Panneau XXL × 4 — 400 €" in page.locator("body").inner_text()

            # Vérifier que le retour ne perd pas la quantité choisie.
            page.locator(".btn-edit-custom").click()
            assert page.locator("#panneaux_xxl").input_value() == "4"
            assert page.locator("#avec_panneaux").is_checked()
            assert page.locator('.selectable-image[data-value="Photobooth"]').evaluate(
                "(card) => card.classList.contains('selected')"
            )
            for _ in range(4):
                page.locator("#nextStep").click()
            page.locator("#submitStep").click()
            page.locator("#btn-confirm").click()
            page.wait_for_url("**/remerciement/")
            close_old_connections()
            event = load_event()
            assert event.event_option.panneaux_xxl == 4
            assert event.event_option.panneaux_forfait == 400
            assert event.event_option.get_selected_options() == "4 panneaux XXL"

            detail_url = f"{base_url}/backend/info-event/{event.id}/"
            assert page.goto(detail_url).ok
            page.locator("#panneaux_remise").fill("25")
            page.locator("#event-save-button").press("Enter")
            page.wait_for_function("document.querySelector('#prix_proposed')?.value === '775'")
            page.screenshot(path=str(RESULTS / "fiche-crm.png"))

            def send_quote(total, deposit, quantity=4, discount=25):
                previous = len(MESSAGES)
                page.locator('form[action*="confirmation/envoi-mail"] button').press("Enter")
                page.locator('form[action*="/envoi-mail/"] button').press("Enter")
                page.get_by_text("E-mail envoyé", exact=True).wait_for()
                assert len(MESSAGES) == previous + 1
                close_old_connections()
                saved = load_event()
                assert saved.prix_proposed == total
                assert saved.status == "Sended"
                check_received_mail(total, deposit, quantity, discount)
                assert page.goto(detail_url).ok

            send_quote(775, 100)

            # Même calcul dans la facture téléchargée par sa véritable route.
            response = page.request.get(
                f"{base_url}/backend/info-event/generate-facture-pdf/{event.id}/"
            )
            assert response.ok
            invoice = response.body()
            invoice_text = "\n".join(
                part.extract_text() for part in PdfReader(BytesIO(invoice)).pages
            )
            assert "Panneau XXL" in invoice_text and "775 €" in invoice_text
            (RESULTS / "facture-775.pdf").write_bytes(invoice)

            # Rejeter une remise trop élevée avant la sauvegarde.
            data = page.locator("#event-update-form").evaluate(
                "(form) => Object.fromEntries(new FormData(form))"
            )
            data["panneaux_remise"] = "401"
            rejected = page.request.post(
                f"{base_url}/backend/info-event/event/update/{event.id}/", form=data,
            )
            assert rejected.status == 400
            close_old_connections()
            assert load_event().event_option.panneaux_remise == 25

            # Contrôler les quatre bornes sur de véritables mails et PDF.
            for total, deposit in [(1000, 150), (999, 100), (600, 100), (599, 50)]:
                page.locator("#prix_brut").fill("650")
                page.locator("#reduc_product").fill("50")
                page.locator("#panneaux_remise").fill("0")
                page.locator("#reduc_all").fill(str(1000 - total))
                page.locator("#event-save-button").press("Enter")
                page.wait_for_function(
                    f"document.querySelector('#prix_proposed')?.value === '{total}'"
                )
                send_quote(total, deposit, discount=0)

            # Supprimer l'option et vérifier son absence du devis reçu.
            page.locator("#panneaux_xxl").select_option("0")
            page.locator("#prix_brut").fill("450")
            page.locator("#reduc_all").fill("0")
            page.locator("#event-save-button").press("Enter")
            page.wait_for_function("document.querySelector('#prix_proposed')?.value === '400'")
            send_quote(400, 50, quantity=0, discount=0)
            close_old_connections()
            option = load_event().event_option
            assert option.panneaux_xxl == 0 and option.panneaux_remise == 0
            assert not errors, errors
            return {"mails_captures": len(MESSAGES), "bornes_acompte": [599, 600, 999, 1000]}
        except Exception:
            page.screenshot(path=str(RESULTS / "echec.png"))
            raise
        finally:
            browser.close()


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    report = {"status": "failed"}
    with TemporaryDirectory(prefix="crm-e2e-") as directory:
        os.environ["CRM_E2E_SQLITE_PATH"] = str(Path(directory) / "test.sqlite3")
        os.environ["DJANGO_SETTINGS_MODULE"] = "tests_e2e.settings"
        import django
        django.setup()
        from tests_e2e.boundaries import install_boundaries
        install_boundaries()
        from django.core.management import call_command
        from django.core.wsgi import get_wsgi_application
        from django.db import connections

        call_command("migrate", run_syncdb=True, verbosity=0)
        with patch("smtplib.SMTP_SSL", CapturedSMTP), patch(
            "smtplib.SMTP", side_effect=AssertionError("SMTP réel interdit")
        ), patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("Appel HTTP externe interdit dans le test"),
        ):
            server = make_server("127.0.0.1", 0, get_wsgi_application())
            worker = Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                report.update(run_browser(f"http://127.0.0.1:{server.server_port}"))
                report["status"] = "passed"
            finally:
                server.shutdown()
                worker.join(timeout=5)
                server.server_close()
                connections.close_all()
                (RESULTS / "resultat.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
                )
    print("Parcours validé : formulaire, CRM, facture, mails capturés et devis PDF.")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
