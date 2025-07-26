# calculators/templatetags/calculator_filters.py
from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adds a CSS class to a Django form field.
    Usage: {{ form.field_name|add_class:"your-css-class" }}
    """
    return field.as_widget(attrs={"class": css_class})