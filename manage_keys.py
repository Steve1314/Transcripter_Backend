import json
import secrets
import os
import argparse

KEYS_FILE = "keys.json"

def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=4)

def generate_key(name):
    keys = load_keys()
    new_key = secrets.token_urlsafe(32)
    keys[new_key] = {
        "name": name,
        "created_at": str(os.path.getmtime(KEYS_FILE)) if os.path.exists(KEYS_FILE) else "now"
    }
    save_keys(keys)
    return new_key

def list_keys():
    keys = load_keys()
    for key, info in keys.items():
        print(f"Name: {info['name']} | Key: {key}")

def revoke_key(key):
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        print(f"Key revoked.")
    else:
        print("Key not found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage API keys for EchoLock API")
    parser.add_argument("--add", help="Add a new key with the given name")
    parser.add_argument("--list", action="store_true", help="List all keys")
    parser.add_argument("--revoke", help="Revoke the given key")
    
    args = parser.parse_args()
    
    if args.add:
        key = generate_key(args.add)
        print(f"Generated key for '{args.add}': {key}")
    elif args.list:
        list_keys()
    elif args.revoke:
        revoke_key(args.revoke)
    else:
        parser.print_help()
