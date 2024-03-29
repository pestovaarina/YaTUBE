from django import template
register = template.Library()


@register.filter
def addclass(field, css):
    '''Фильтр, который дает возможность указывать
    CSS-класс в HTML-коде любого поля формы.'''
    return field.as_widget(attrs={'class': css})
