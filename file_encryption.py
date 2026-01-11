import argparse
import os
import base64
import secrets
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet


# Crypto Helpers


def derive_key(password: str, salt: bytes, iterations: int = 390000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# Encryption


def encrypt_file(args):
    if not os.path.exists(args.input):
        raise FileNotFoundError("Input file not found")

    with open(args.input, "rb") as f:
        data = f.read()

    salt = secrets.token_bytes(16)
    key = derive_key(args.password, salt)
    encrypted = Fernet(key).encrypt(data)

    filename = os.path.basename(args.input).encode()
    out_path = args.output or (args.input + ".enc")

    with open(out_path, "wb") as f:
        f.write(b"FILE")
        f.write(salt)
        f.write(len(filename).to_bytes(2, "big"))
        f.write(filename)
        f.write(encrypted)

    print(f"[+] File encrypted successfully → {out_path}")


# Decryption


def decrypt_file(args):
    if not os.path.exists(args.input):
        raise FileNotFoundError("Encrypted file not found")

    with open(args.input, "rb") as f:
        magic = f.read(4)
        if magic != b"FILE":
            raise ValueError("Invalid encrypted file format")

        salt = f.read(16)
        name_len = int.from_bytes(f.read(2), "big")
        original_name = f.read(name_len).decode()
        encrypted = f.read()

    key = derive_key(args.password, salt)
    decrypted = Fernet(key).decrypt(encrypted)

    out_dir = args.output or os.path.dirname(args.input)
    out_path = os.path.join(out_dir, original_name)

    with open(out_path, "wb") as f:
        f.write(decrypted)

    print(f"[+] File decrypted successfully → {out_path}")


# CLI


def main():
    parser = argparse.ArgumentParser(description="Shadow File Encryption CLI")

    sub = parser.add_subparsers(dest="cmd", required=True)

    # Encrypt command
    enc = sub.add_parser("encrypt", help="Encrypt a file")
    enc.add_argument("--input", required=True, help="Input file path")
    enc.add_argument("--password", required=True, help="Encryption password")
    enc.add_argument("--output", help="Output encrypted file (.enc)")

    # Decrypt command
    dec = sub.add_parser("decrypt", help="Decrypt a file")
    dec.add_argument("--input", required=True, help="Encrypted .enc file")
    dec.add_argument("--password", required=True, help="Decryption password")
    dec.add_argument("--output", help="Output directory")

    args = parser.parse_args()

    try:
        if args.cmd == "encrypt":
            encrypt_file(args)
        elif args.cmd == "decrypt":
            decrypt_file(args)
    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    main()
  
