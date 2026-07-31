document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("event-update-form");
    const saveButton = document.getElementById("event-save-button");
    const saveState = document.getElementById("event-save-state");
    const floralCheckbox = document.getElementById("mur_floral_checkbox");
    const floralStyle = document.getElementById("mur_floral_style");

    const markAsChanged = () => {
        if (!saveState) return;
        saveState.classList.add("is-dirty");
        saveState.querySelector("i")?.classList.replace("fa-check-circle", "fa-exclamation-circle");
        const label = saveState.querySelector("span");
        if (label) label.textContent = "Modifications non enregistrées.";
    };

    form?.addEventListener("input", markAsChanged);
    form?.addEventListener("change", markAsChanged);

    form?.addEventListener("submit", () => {
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.querySelector("i")?.classList.replace("fa-save", "fa-spinner");
            saveButton.querySelector("i")?.classList.add("fa-spin");
            const label = saveButton.querySelector("span");
            if (label) label.textContent = "Enregistrement…";
        }

        if (saveState) {
            saveState.classList.remove("is-dirty");
            const label = saveState.querySelector("span");
            if (label) label.textContent = "Sauvegarde locale puis synchronisation en arrière-plan…";
        }
    });

    const updateFloralStyle = () => {
        if (floralStyle && floralCheckbox) {
            floralStyle.disabled = !floralCheckbox.checked;
        }
    };

    floralCheckbox?.addEventListener("change", updateFloralStyle);
    updateFloralStyle();

    document.querySelectorAll("[data-copy-target]").forEach((button) => {
        button.addEventListener("click", async () => {
            const target = document.getElementById(button.dataset.copyTarget);
            if (!target?.value) return;

            try {
                await navigator.clipboard.writeText(target.value);
            } catch (_error) {
                target.select();
                document.execCommand("copy");
            }

            const previousHtml = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check" aria-hidden="true"></i> Copié';
            window.setTimeout(() => {
                button.innerHTML = previousHtml;
            }, 1600);
        });
    });
});
