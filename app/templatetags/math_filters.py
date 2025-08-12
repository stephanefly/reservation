from django import template
from decimal import Decimal

register = template.Library()

def to_decimal(val):
    try:
        return Decimal(str(val)) if val is not None else Decimal("0")
    except:
        return Decimal("0")

@register.simple_tag
def subtract_three(value, arg1, arg2):
    return to_decimal(value) - to_decimal(arg1) - to_decimal(arg2)

@register.simple_tag
def total_to_me(events, salary):
    """
    Calcule le total à me donner pour un membre :
    montant restant - membre_salary - charge
    """
    total = Decimal("0")
    sal = to_decimal(salary)

    for e in events or []:
        montant = to_decimal(getattr(getattr(e, "event_acompte", None), "montant_restant", 0))
        epp = getattr(e, "event_post_presta", None)
        membre_salary = to_decimal(getattr(epp, "membre_salary", 0))
        charge = to_decimal(getattr(epp, "charge", 0))

        total += montant - membre_salary - charge
    return total