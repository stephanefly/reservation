// ✅ formulaire.js (à placer dans static/js/formulaire.js)

console.log("✅ formulaire.js bien chargé !");

document.addEventListener('DOMContentLoaded', function () {
    setupClientTypeToggle();
    setupSliders();
    setupMagnetsSlider();
    setupSelectableImages();
    setupSelectableOption();
    rangeLivraison();
    setupLivraisonLock();
    setupFormValidation();
});

function setupClientTypeToggle() {
    const personneRadio = document.getElementById('id_personne');
    const entrepriseRadio = document.getElementById('id_entreprise');
    const nomPrenomRow = document.getElementById('nomPrenomRow');
    const raisonSocialeRow = document.getElementById('raisonSocialeRow');
    const nomInput = document.getElementById('id_nom');
    const prenomInput = document.getElementById('id_prenom');
    const raisonSocialeInput = document.getElementById('id_raison_sociale');

    function updateFormFields() {
        if (entrepriseRadio.checked) {
            nomPrenomRow.style.display = 'none';
            nomInput.removeAttribute('required');
            prenomInput.removeAttribute('required');
            raisonSocialeRow.style.display = '';
            raisonSocialeInput.setAttribute('required', '');
        } else {
            nomPrenomRow.style.display = '';
            nomInput.setAttribute('required', '');
            prenomInput.setAttribute('required', '');
            raisonSocialeRow.style.display = 'none';
            raisonSocialeInput.removeAttribute('required');
        }
    }

    personneRadio.addEventListener('change', updateFormFields);
    entrepriseRadio.addEventListener('change', updateFormFields);
    updateFormFields();
}

function setupSliders() {
    const slider = document.getElementById("heureRange");
    const output = document.getElementById("heureValue");
    slider.addEventListener('input', () => {
        output.textContent = slider.value;
    });
}

function setupMagnetsSlider() {
    const slider = document.getElementById("MagnetsRange");
    const output = document.getElementById("MagnetsNumber");
    slider.addEventListener('input', () => {
        output.textContent = slider.value;
    });
}

function setupSelectableImages() {
    document.querySelectorAll('.selectable-image').forEach(item => {
        item.addEventListener('click', () => {
            item.classList.toggle('selected');
            updateHiddenInputs('selectedImages', '.selectable-image');
            setupLivraisonLock();
        });
    });
}

function setupSelectableOption() {
    document.querySelectorAll('.selectable-option').forEach(item => {
        item.addEventListener('click', () => {
            item.classList.toggle('selected');
            updateHiddenInputs('selectedOption', '.selectable-option');
        });
    });
}

function updateHiddenInputs(hiddenInputId, selector) {
    const selected = document.querySelectorAll(`${selector}.selected`);
    const values = Array.from(selected).map(el => el.getAttribute('data-value'));
    document.getElementById(hiddenInputId).value = values.join(',');
}

function setupLivraisonLock() {
    const livraisonCheckbox = document.getElementById('livraisonInstallation');
    const slider = document.getElementById('heureRange');
    const heureSpan = document.getElementById('heureValue');

    function updateLivraisonState() {
        const isMiroirSelected = document.querySelector('.selectable-image[data-value="Miroirbooth"]')?.classList.contains('selected');
        const is360Selected = document.querySelector('.selectable-image[data-value="360Booth"]')?.classList.contains('selected');
        const is360AirboothSelected = document.querySelector('.selectable-image[data-value="360Airbooth"]')?.classList.contains('selected');
        const isVogueboothSelected = document.querySelector('.selectable-image[data-value="Voguebooth"]')?.classList.contains('selected');

        if (isMiroirSelected || is360Selected || is360AirboothSelected || isVogueboothSelected) {
            livraisonCheckbox.checked = true;
            livraisonCheckbox.disabled = true;
            slider.disabled = false;
            heureSpan.textContent = slider.value;
        } else {
            livraisonCheckbox.disabled = false;
            if (!livraisonCheckbox.checked) {
                slider.disabled = true;
                heureSpan.textContent = "toute la soirée - -";
            }
        }
    }

    document.querySelectorAll('.selectable-image').forEach(item => {
        item.addEventListener('click', updateLivraisonState);
    });

    livraisonCheckbox.addEventListener('change', updateLivraisonState);
    slider.addEventListener('input', () => {
        if (!slider.disabled) {
            heureSpan.textContent = slider.value;
        }
    });

    updateLivraisonState();
}

function rangeLivraison() {
    const livraisonCheckbox = document.getElementById('livraisonInstallation');
    const slider = document.getElementById('heureRange');
    const heureSpan = document.getElementById('heureValue');

    livraisonCheckbox.addEventListener('change', () => {
        if (livraisonCheckbox.checked) {
            slider.disabled = false;
            heureSpan.textContent = slider.value;
        } else {
            slider.disabled = true;
            heureSpan.textContent = "toute la soirée - -";
        }
    });

    slider.addEventListener('input', () => {
        if (livraisonCheckbox.checked) {
            heureSpan.textContent = slider.value;
        }
    });
}

function setupFormValidation() {
    const form = document.getElementById('monFormulaire');
    form.addEventListener('submit', function (event) {
        const selected = document.querySelectorAll('.selectable-image.selected');
        if (selected.length === 0) {
            event.preventDefault();
            alert("Merci de sélectionner au moins une prestation dans la section CHOIX DE LA PRESTATION.");
            const target = document.querySelector('.image-select-container');
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                target.style.border = '3px solid red';
                setTimeout(() => {
                    target.style.border = 'none';
                }, 3000);
            }
            return false;
        }
    });
}
