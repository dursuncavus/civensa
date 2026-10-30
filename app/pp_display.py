"""Shared presentation labels for performance programme screens."""

STATUS_LABELS = {
    "draft": "Taslak",
    "submitted": "İncelemede",
    "returned": "İade edildi",
    "approved": "Onaylandı",
    "approve": "Onaylandı",
    "return": "İade edildi",
    "active": "Etkin",
    "closed": "Kapalı",
    "pending": "Bekliyor",
    "verified": "Doğrulandı",
    "preview": "Önizleme",
    "applied": "Uygulandı",
    "reverted": "Geri alındı",
    "required": "Kart gerekli",
    "zero": "Sıfır bütçeli",
    "excluded": "Kapsam dışı",
    "not_started": "Başlamadı",
    "in_progress": "Veri girişi devam ediyor",
    "needs_attention": "Eksikleri / hataları var",
    "ready": "Hazır",
    "blocked": "Engellendi",
    "ok": "Sağlıklı",
    "error": "Hata",
    "degraded": "Aksama var",
}


def status_label(value):
    return STATUS_LABELS.get(value, f"Bilinmeyen durum ({value})")


EVENT_LABELS = {
    "submitted": "İncelemeye gönderildi",
    "approve": "Onaylandı",
    "return": "İade edildi",
}


def event_label(value):
    return EVENT_LABELS.get(value, f"Bilinmeyen işlem ({value})")


def actor_label(user):
    if user is None:
        return "Sistem"
    position = getattr(user, "position", None)
    title = {"director": "Müdür", "staff": "Personel"}.get(position, position)
    return f"{user.full_name} ({title})" if title else user.full_name
