from django.contrib import admin
from .models import SeasonalSignal, Symbol


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ('financial_instrument', 'company_name', 'exchange')
    search_fields = ('financial_instrument', 'company_name', 'exchange')
    ordering = ('financial_instrument',)


@admin.register(SeasonalSignal)
class SeasonalSignalAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'magic_number', 'direction', 'entry_month', 'entry_day',
        'takeprofit_month', 'takeprofit_day', 'stoploss', 'stoploss_type',
        'risk'
    )
    list_filter = ('direction', 'stoploss_type', 'entry_month')
    search_fields = ('magic_number', 'symbol__financial_instrument')
    ordering = ('-id',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('magic_number', 'symbol', 'direction')
        }),
        ('Параметры входа/выхода', {
            'fields': (
                ('entry_month', 'entry_day'),
                ('takeprofit_month', 'takeprofit_day'),
                ('open_time', 'close_time')
            )
        }),
        ('Риск-менеджмент', {
            'fields': ('stoploss', 'stoploss_type', 'risk')
        })
    )
