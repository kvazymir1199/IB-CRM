from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Фильтр для получения значения из словаря по ключу.
    Используется в шаблонах для доступа к значениям словаря.
    
    Пример использования:
    {{ dictionary|get_item:key }}
    """
    return dictionary.get(key) 