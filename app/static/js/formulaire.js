function setupClientTypeToggle() {
    var personneRadio = document.getElementById('id_personne');
    var entrepriseRadio = document.getElementById('id_entreprise');
    var nomPrenomRow = document.getElementById('nomPrenomRow');
    var raisonSocialeRow = document.getElementById('raisonSocialeRow');
    var nomInput = document.getElementById('id_nom');
    var prenomInput = document.getElementById('id_prenom');
    var raisonSocialeInput = document.getElementById('id_raison_sociale');

    function updateFormFields() {
        // Vérifier si le bouton radio 'entreprise' est sélectionné
        if (entrepriseRadio.checked) {
            // Masquer les champs 'Nom' et 'Prénom'
            nomPrenomRow.style.display = 'none';
            // Retirer l'attribut 'required' pour 'Nom' et 'Prénom'
            nomInput.removeAttribute('required');
            prenomInput.removeAttribute('required');
            // Afficher le champ 'Raison Sociale' et le rendre requis
            raisonSocialeRow.style.display = '';
            raisonSocialeInput.setAttribute('required', '');
        } else {
            // Afficher les champs 'Nom' et 'Prénom'
            nomPrenomRow.style.display = '';
            // Ajouter l'attribut 'required' pour 'Nom' et 'Prénom'
            nomInput.setAttribute('required', '');
            prenomInput.setAttribute('required', '');
            // Masquer le champ 'Raison Sociale' et retirer l'attribut 'required'
            raisonSocialeRow.style.display = 'none';
            raisonSocialeInput.removeAttribute('required');
        }
    }

    // Ajouter des écouteurs d'événements aux boutons radio
    personneRadio.addEventListener('change', updateFormFields);
    entrepriseRadio.addEventListener('change', updateFormFields);

    // Appel initial pour configurer l'état correct du formulaire dès le chargement de la page
    updateFormFields();
}


function setupSliders() {
    var slider = document.getElementById("heureRange");
    var output = document.getElementById("heureValue");

    slider.oninput = function() {
        output.innerHTML = this.value;
    };
}


// Mise à jour du texte de l'élément span en fonction de la valeur du slider
function setupMagnetsSlider() {
    var slider_magnet = document.getElementById("MagnetsRange");
    var output_magnet = document.getElementById("MagnetsNumber");

    slider_magnet.oninput = function() {
        output_magnet.textContent = this.value;
    };
}


// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    setupClientTypeToggle();
    setupSliders();
    setupMagnetsSlider();
});