// Gestion des radios pour afficher/masquer les champs
function setupClientTypeToggle() {
    var personneRadio = document.getElementById('id_personne');
    var entrepriseRadio = document.getElementById('id_entreprise');
    var nomPrenomRow = document.getElementById('nomPrenomRow');
    var raisonSocialeRow = document.getElementById('raisonSocialeRow');

    personneRadio.addEventListener('change', function() {
        nomPrenomRow.style.display = 'block';
        raisonSocialeRow.style.display = 'none';
    });

    entrepriseRadio.addEventListener('change', function() {
        nomPrenomRow.style.display = 'none';
        raisonSocialeRow.style.display = 'block';
    });
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

// Mise à jour du texte de l'élément span en fonction de la valeur du slider
function setupMagnetsSlider() {
    var slider_magnet = document.getElementById("MagnetsRange");
    var output_magnet = document.getElementById("MagnetsNumber");

    slider_magnet.oninput = function() {
        output_magnet.textContent = this.value;
    };
}

// Gestion des sliders
function setupSliders() {
    var slider = document.getElementById("heureRange");
    var output = document.getElementById("heureValue");

    output.innerHTML = slider.value;
    slider.oninput = function() {
        output.innerHTML = this.value;
    };
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


function disableLivraison() {
    var selectedValues = document.getElementById('selectedImages').value;
    var livraisonCheckbox = document.getElementById('livraisonInstallation');

    if (selectedValues.includes("Miroirbooth") || selectedValues.includes("360Booth")) {
        livraisonCheckbox.checked = true;
        livraisonCheckbox.disabled = true; // Assure que le checkbox est activé pour permettre la désélection manuelle si nécessaire
    } else if (!selectedValues.includes("Photobooth")) {
        livraisonCheckbox.disabled = false;
    }
    rangeLivraison();
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    setupClientTypeToggle();
    setupSelectableImages();
    setupSliders();
    setupMagnetsSlider();
    rangeLivraison();
    disableLivraison();
});
