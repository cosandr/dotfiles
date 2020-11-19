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
cd ~andrei/.local/share/chezmoi
CHEZMOI_HOME=. ./update_config.py
chezmoi --source ~andrei/.local/share/chezmoi apply
```

# gpg-agent

On Windows start `"C:\Program Files (x86)\GnuPG\bin\gpgconf.exe" --launch gpg-agent` with Task Scheduler at login

See [this](https://superuser.com/a/1329299) post.

- Export public key `gpg --export 273D94492E01567B > pub`
- Copy to server
- Import `gpg --import pub`
- Set trust `gpg --edit-key 273D94492E01567B`, trust, 5, save
- Edit `sshd_config` on server
```
Match User andrei
    StreamLocalBindUnlink yes
```
- Ensure gpg-agent doesn't start on server
```sh
systemctl --global mask --now gpg-agent.service gpg-agent.socket gpg-agent-ssh.socket gpg-agent-extra.socket gpg-agent-browser.socket
```
- Test with `echo test | gpg --clearsign`
