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
function setupMagnetsSlider() {
    var slider_magnet = document.getElementById("MagnetsRange");
    var output_magnet = document.getElementById("MagnetsNumber");

    slider_magnet.oninput = function() {
        output_magnet.textContent = this.value;
    };
}


function setupSliders() {
    var slider = document.getElementById("heureRange");
    var output = document.getElementById("heureValue");

    slider.oninput = function() {
        output.innerHTML = this.value;
    };
}

// Gestion des images sélectionnables
function setupSelectableImages() {
    document.querySelectorAll('.selectable-image').forEach(function(item) {
        item.addEventListener('click', function() {
            this.classList.toggle('selected');
            let selected = document.getElementById('selectedImages');
            let value = this.getAttribute('data-value');
            let selectedValues = selected.value ? selected.value.split(',') : [];

            if (selectedValues.includes(value)) {
                selectedValues = selectedValues.filter(function(val) { return val !== value; });
            } else {
                selectedValues.push(value);
            }

            selected.value = selectedValues.join(',');
            disableLivraison();
        });
    });
}


function rangeLivraison() {
    var livraisonInstallationCheckbox = document.getElementById('livraisonInstallation');
    var heureRangeSlider = document.getElementById('heureRange');
    var heureValueSpan = document.getElementById('heureValue');

    // Fonction pour mettre à jour l'état du slider et du texte
    function updateSliderState() {
        if (livraisonInstallationCheckbox.checked) {
            heureRangeSlider.disabled = false; // Active le slider
            heureValueSpan.innerHTML = heureRangeSlider.value; // Affiche les heures
        } else {
            heureRangeSlider.disabled = true; // Désactive le slider
            heureValueSpan.innerHTML = 'toute la soirée - -  '; // Change le texte
        }
    }

    // Événement change sur la case à cocher
    livraisonInstallationCheckbox.addEventListener('change', updateSliderState);

    // Événement input sur le slider pour mettre à jour le texte des heures
    heureRangeSlider.addEventListener('input', function() {
        if (livraisonInstallationCheckbox.checked) {
            heureValueSpan.innerHTML = this.value;
        }
    });

    // Met à jour l'état initial du slider et du texte
    updateSliderState();
}


function setupLivraisonLock() {
    var selectableImages = document.querySelectorAll('.selectable-image');
    var livraisonCheckbox = document.getElementById('livraisonInstallation');
    var heureRangeSlider = document.getElementById('heureRange');
    var heureValueSpan = document.getElementById('heureValue');

    // Mise à jour de l'état du curseur et du texte des heures en fonction de la sélection
    function updateSliderState() {
        var isMiroirboothSelected = document.querySelector('.selectable-image[data-value="Miroirbooth"]').classList.contains('selected');
        var is360BoothSelected = document.querySelector('.selectable-image[data-value="360Booth"]').classList.contains('selected');

        if (isMiroirboothSelected || is360BoothSelected) {
            livraisonCheckbox.checked = true;
            livraisonCheckbox.disabled = true;
            heureRangeSlider.disabled = false; // S'assure que le slider reste actif
            heureValueSpan.innerHTML = heureRangeSlider.value; // Met à jour les heures affichées
        } else {
            livraisonCheckbox.disabled = false;
            // Pas besoin de désactiver le slider ici, car sa disponibilité devrait dépendre uniquement de la case à cocher livraison
        }
    }

    // Ajoute des écouteurs d'événements pour chaque image sélectionnable
    selectableImages.forEach(function(item) {
        item.addEventListener('click', function() {
            // Vérifie la sélection et met à jour l'état du curseur et de la case à cocher
            updateSliderState();
        });
    });

    // Écoute les changements de la case à cocher livraison pour ajuster le slider d'heures
    livraisonCheckbox.addEventListener('change', updateSliderState);

    // Écoute les changements sur le slider pour mettre à jour le texte des heures
    heureRangeSlider.addEventListener('input', function() {
        if (!heureRangeSlider.disabled) {
            heureValueSpan.innerHTML = this.value;
        }
    });

    // Vérification initiale en cas de pré-sélection ou de rechargement de la page avec des sélections en cache
    updateSliderState();
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    setupClientTypeToggle();
    setupSliders();
    setupMagnetsSlider();
    setupSelectableImages();
    rangeLivraison();
    setupLivraisonLock();
});