#!/usr/bin/env python3
"""Generate VAPID keys for web push notifications."""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def generate_vapid_keys():
    """Generate a new VAPID key pair."""
    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key (uncompressed format for web push)
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Base64 URL-safe encoding
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    return public_key_b64, private_key_b64

if __name__ == '__main__':
    print("=" * 80)
    print("VAPID Key Generator for Web Push Notifications")
    print("=" * 80)
    print("\nGenerating new VAPID key pair...\n")
    
    public_key, private_key = generate_vapid_keys()
    
    print("✅ Keys generated successfully!\n")
    print("-" * 80)
    print("PUBLIC KEY (for frontend - base.html):")
    print("-" * 80)
    print(public_key)
    print()
    print("-" * 80)
    print("PRIVATE KEY (for backend - settings.py):")
    print("-" * 80)
    print(private_key)
    print()
    print("-" * 80)
    print("\nAdd these to your settings.py:")
    print("-" * 80)
    print(f'VAPID_PUBLIC_KEY = "{public_key}"')
    print(f'VAPID_PRIVATE_KEY = "{private_key}"')
    print('VAPID_ADMIN_EMAIL = "admin@yeninesilevim.com"')
    print("-" * 80)
    print("\n⚠️  IMPORTANT:")
    print("1. Update settings.py with these keys")
    print("2. Delete old subscriptions: PushSubscription.objects.all().delete()")
    print("3. Restart gunicorn: sudo systemctl restart gunicorn")
    print("4. Users must re-subscribe with 'Stok Uyarılarını Aktif Et' button")
    print("=" * 80)
