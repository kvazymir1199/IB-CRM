from django.core.management.base import BaseCommand
from signals.models import Symbol


class Command(BaseCommand):
    help = 'Импорт списка финансовых инструментов'

    def handle(self, *args, **options):
        symbols_data = [
            {
                'financial_instrument': 'MHNG',
                'company_name': 'Micro Henry Hub Natural Gas',
                'exchange': 'NYMEX'
            },
            {
                'financial_instrument': 'SB',
                'company_name': 'Sugar No. 11',
                'exchange': 'NYBOT'
            },
            {
                'financial_instrument': 'LE',
                'company_name': 'Live Cattle',
                'exchange': 'CME'
            },
            {
                'financial_instrument': 'BUK100P',
                'company_name': 'CBOE UK 100 Index',
                'exchange': 'CEDX'
            },
            {
                'financial_instrument': 'MES',
                'company_name': 'Micro E-Mini S&P 500 Stock Price',
                'exchange': 'CME'
            },
            {
                'financial_instrument': 'SI',
                'company_name': 'Silver Index',
                'exchange': 'COMEX'
            },
            {
                'financial_instrument': 'MGC',
                'company_name': 'E-Micro Gold',
                'exchange': 'COMEX'
            },
            {
                'financial_instrument': 'PA',
                'company_name': 'Palladium Index',
                'exchange': 'NYMEX'
            },
            {
                'financial_instrument': 'PL',
                'company_name': 'Platinum Index',
                'exchange': 'NYMEX'
            },
            {
                'financial_instrument': 'DAX',
                'company_name': 'DAX 40 Index (Deutsche Aktien Xchange)',
                'exchange': 'EUREX'
            },
            {
                'financial_instrument': 'MNQ',
                'company_name': 'Micro E-Mini Nasdaq-100 Index',
                'exchange': 'CME'
            },
            {
                'financial_instrument': 'MCL',
                'company_name': 'Micro WTI Crude Oil',
                'exchange': 'NYMEX'
            },
            {
                'financial_instrument': 'CC',
                'company_name': 'Cocoa NYBOT',
                'exchange': 'NYBOT'
            },
            {
                'financial_instrument': 'KC',
                'company_name': 'Coffee "C"',
                'exchange': 'NYBOT'
            },
            {
                'financial_instrument': 'YK',
                'company_name': 'Mini Sized Soybean Futures',
                'exchange': 'CBOT'
            },
            {
                'financial_instrument': 'YC',
                'company_name': 'Mini Sized Corn Futures',
                'exchange': 'CBOT'
            },
            {
                'financial_instrument': 'YW',
                'company_name': 'Mini Sized Wheat Futures',
                'exchange': 'CBOT'
            },
            {
                'financial_instrument': 'CT',
                'company_name': 'Cotton No. 2',
                'exchange': 'NYBOT'
            },
            {
                'financial_instrument': 'MHG',
                'company_name': 'Micro Copper',
                'exchange': 'COMEX'
            },
            {
                'financial_instrument': 'RB',
                'company_name': 'NYMEX RBOB Gasoline Index',
                'exchange': 'NYMEX'
            },
            {
                'financial_instrument': 'HE',
                'company_name': 'Lean Hogs',
                'exchange': 'CME'
            },
            {
                'financial_instrument': 'OJ',
                'company_name': 'FC Orange Juice "A"',
                'exchange': 'NYBOT'
            },
            {
                'financial_instrument': 'ZB',
                'company_name': 'US Treasury Bond',
                'exchange': 'CBOT'
            },
            {
                'financial_instrument': 'HO',
                'company_name': 'Heating Oil',
                'exchange': 'NYMEX'
            },
            {
                'financial_instrument': 'ZL',
                'company_name': 'Soybean Oil Futures',
                'exchange': 'CBOT'
            },
            {
                'financial_instrument': 'GF',
                'company_name': 'Feeder Cattle',
                'exchange': 'CME'
            },
            {
                'financial_instrument': 'LBR',
                'company_name': 'Lumber Futures',
                'exchange': 'CME'
            }
        ]

        created_count = 0
        updated_count = 0

        for symbol_data in symbols_data:
            symbol, created = Symbol.objects.update_or_create(
                financial_instrument=symbol_data['financial_instrument'],
                defaults={
                    'company_name': symbol_data['company_name'],
                    'exchange': symbol_data['exchange']
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        msg = (
            f'Successfully imported symbols. '
            f'Created: {created_count}, Updated: {updated_count}'
        )
        self.stdout.write(self.style.SUCCESS(msg)) 