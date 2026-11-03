import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.module.data_bdd.instant_quote import (
    calculer_devis_instantane,
    devis_automatique_autorise,
    preparer_et_envoyer_devis,
)


def exemple(source="INSTAGRAM", entreprise=False, duree=5, postcode=75001, **produits):
    # Les vrais modèles possèdent ces champs et méthodes. L'option est simulée
    # pour vérifier le calcul et la décision, sans BDD ni envoi SMTP.
    option = SimpleNamespace(duree=duree, panneaux_xxl=0,
                             magnets=0, PorteCles=0, MagnetsSimple=0)
    for nom in (
        "MurFloral", "Phonebooth", "LivreOr", "Fond360", "PanneauBienvenue",
        "Holo3D", "PanneauFontaine", "VideoLivreOr",
        "PhotographeVoguebooth", "ImpressionVoguebooth", "DecorVoguebooth",
    ):
        setattr(option, nom, False)
    for key in ("photobooth", "miroirbooth", "videobooth", "voguebooth", "ipadbooth", "airbooth"):
        produits.setdefault(key, False)
    event = SimpleNamespace(
        client=SimpleNamespace(how_find=source, raison_sociale=entreprise),
        event_details=SimpleNamespace(code_postal_evenement=postcode),
        event_product=SimpleNamespace(**produits),
        event_option=option,
        status="Initied",
        save=Mock(),
    )
    return event


class InstantQuoteTests(unittest.TestCase):
    def test_recommandation_ne_declenche_jamais_devis_automatique(self):
        for source in ("RECOMMANDATION", " recommandation ", "Recommandation"):
            event = exemple(source=source, photobooth=True)
            envoyer = Mock(return_value=True)
            self.assertFalse(devis_automatique_autorise(event.client))
            self.assertFalse(preparer_et_envoyer_devis(event, envoyer))
            envoyer.assert_not_called()
            event.save.assert_not_called()

    def test_professionnel_reste_manuel(self):
        event = exemple(entreprise=True, photobooth=True)
        self.assertFalse(preparer_et_envoyer_devis(event, Mock()))
        event.save.assert_not_called()

    def test_photobooth_standard_et_transport_inclus(self):
        event = exemple(photobooth=True)
        self.assertEqual(calculer_devis_instantane(event), {
            "prix_brut": 450, "reduc_product": 50, "prix_proposed": 400,
        })

    def test_tarif_3h_photobooth(self):
        event = exemple(photobooth=True, duree=3)
        self.assertEqual(calculer_devis_instantane(event)["prix_proposed"], 350)

    def test_pack_plusieurs_prestations(self):
        event = exemple(photobooth=True, miroirbooth=True)
        result = calculer_devis_instantane(event)
        self.assertEqual(result["prix_brut"], 1000)
        self.assertEqual(result["prix_proposed"], 1000)

    def test_envoi_reussi_change_le_statut(self):
        event = exemple(photobooth=True)
        mail = Mock(return_value=True)
        self.assertTrue(preparer_et_envoyer_devis(event, mail))
        mail.assert_called_once_with(event, "devis")
        self.assertEqual(event.status, "Sended")
        self.assertEqual(event.prix_proposed, 400)

    def test_envoi_echoue_conserve_le_devis_en_calcul_pour_suivi(self):
        event = exemple(photobooth=True)
        self.assertFalse(preparer_et_envoyer_devis(event, Mock(return_value=False)))
        self.assertEqual(event.status, "Calculed")

    def test_sources_inconnues_et_code_postal_douteux_sont_manuel(self):
        self.assertFalse(devis_automatique_autorise(exemple(source="").client))
        event = exemple(photobooth=True, postcode=1000)
        with self.assertRaises(ValueError):
            calculer_devis_instantane(event)


if __name__ == "__main__":
    unittest.main()
