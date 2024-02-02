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
        });
    });
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
    setupSelectableImages();
    setupSliders();
    setupMagnetsSlider();
});
