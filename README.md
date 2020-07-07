# Secrets

Assuming `.secrets_pass` contains the password in plain text

### Encrypt

```sh
gpg --passphrase-file .secrets_pass --batch --yes --symmetric --cipher-algo AES256 -o secrets.json.gpg .secrets.json
```

### Decrypt

The Python script will decrypt it for you if `secrets.json.gpg` exists but `.secrets.json` doesn't.

```sh
# To stdout
gpg --passphrase-file .secrets_pass --batch -d secrets.json.gpg
# To file
gpg --passphrase-file .secrets_pass --batch --yes -o .secrets.json -d secrets.json.gpg
```

### Example

Same structure as config file.

```json
{
    "data": {
        "dresrv": {
            "domain": "",
            "local_ip": "",
            "ssh_port": ""
        },
        "git": {
            "private_email": "",
            "private_name": "",
            "public_email": "",
            "public_name": ""
        }
    }
}
```

# First run as root

If we want to use another user's chezmoi, here `andrei`

```sh
chezmoi --source ~andrei/.local/share/chezmoi apply
```
