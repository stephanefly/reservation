OPTION_NAMES = (
    "MurFloral",
    "Phonebooth",
    "LivreOr",
    "Fond360",
    "PanneauBienvenue",
    "Holo3D",
    "PanneauFontaine",
    "VideoLivreOr",
    "PhotographeVoguebooth",
    "ImpressionVoguebooth",
    "DecorVoguebooth",
)


def parse_int(value, default=0):
    try:
        return int(value) if value is not None and str(value).strip() else default
    except (ValueError, TypeError):
        return default


def calculate_option_total(event_option):
    total = 0

    for option_name in OPTION_NAMES:
        if getattr(event_option, option_name):
            base_price = getattr(event_option, f"prix_base_{option_name}")()
            reduction = getattr(event_option, f"{option_name}_reduc_prix") or 0
            total += base_price - reduction

    for quantity_name, price_method_name in (
        ("magnets", "prix_base_magnets"),
        ("PorteCles", "prix_base_PorteCles"),
        ("MagnetsSimple", "prix_base_MagnetsSimple"),
    ):
        quantity = getattr(event_option, quantity_name) or 0
        if quantity:
            base_price = getattr(event_option, price_method_name)(quantity)
            reduction = getattr(event_option, f"{quantity_name}_reduc_prix") or 0
            total += base_price - reduction

    return total


def update_event_option(request, event_option):
    for option_name in OPTION_NAMES:
        setattr(event_option, option_name, request.POST.get(option_name) == "on")
        setattr(
            event_option,
            f"{option_name}_reduc_prix",
            parse_int(request.POST.get(f"{option_name}_reduc_prix")),
        )

    for quantity_name in ("magnets", "PorteCles", "MagnetsSimple"):
        setattr(event_option, quantity_name, parse_int(request.POST.get(quantity_name)))
        setattr(
            event_option,
            f"{quantity_name}_reduc_prix",
            parse_int(request.POST.get(f"{quantity_name}_reduc_prix")),
        )

    event_option.mur_floral_style = (
        request.POST.get("mur_floral_style") if event_option.MurFloral else None
    )
    event_option.livraison = request.POST.get("livraison") == "on"
    event_option.duree = parse_int(request.POST.get("duree"))

    total = calculate_option_total(event_option)
    event_option.save()
    return total
