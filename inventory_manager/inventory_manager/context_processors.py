from django.conf import settings


def webpush_settings(request):
    """
    VAPID public key'i tüm template'lerde kullanılabilir yapar.
    base.html'deki subscribeToPush() fonksiyonu için gerekli.
    """
    return {
        'VAPID_PUBLIC_KEY': settings.VAPID_PUBLIC_KEY
    }
