"""Turkish labels for stored value dimensions; never expose internal enum names."""
VALUE_KIND_LABELS = {
    'actual': 'Gerçekleşme', 'target': 'Hedef', 'forecast': 'Tahmin',
    'budget': 'Bütçe', 'year_end_estimate': 'Yıl Sonu Tahmini',
    'midyear_spend': 'Haziran Sonu Harcama', 'planned': 'Planlanan', 'value': 'Değer',
}
FUNDING_LABELS = {'inside': 'Bütçe İçi', 'outside': 'Bütçe Dışı', 'total': 'Toplam'}


def value_kind_label(kind):
    return VALUE_KIND_LABELS.get(kind, 'Değer')


def funding_label(funding):
    return FUNDING_LABELS.get(funding, 'Kaynak')
