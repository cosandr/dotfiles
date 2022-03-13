# Secrets

Assuming `.secrets.pass` contains the password in plain text

### Encrypt

```sh
gpg --armor --symmetric --passphrase-file .secrets.pass --batch --yes --cipher-algo AES256 -o secrets.json.gpg .secrets.json
```

### Decrypt

The Python script will decrypt it for you if `secrets.json.gpg` exists but `.secrets.json` doesn't.

```sh
# To stdout
gpg --passphrase-file .secrets.pass --batch -d secrets.json.gpg
# To file
gpg --passphrase-file .secrets.pass --batch --yes -o .secrets.json -d secrets.json.gpg
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
            "main_email": "",
            "main_name": "",
            "alt_email": "",
            "alt_name": ""
        }
    }
}
```

# First run as root

If we want to use another user's chezmoi, here `andrei`

```sh
cd ~andrei/.local/share/chezmoi
CHEZMOI_HOME=. ./update_secrets.py
chezmoi --source ~andrei/.local/share/chezmoi apply
```

# gpg-agent

On Windows start `"C:\Program Files (x86)\GnuPG\bin\gpgconf.exe" --launch gpg-agent` with Task Scheduler at login

See [this](https://superuser.com/a/1329299) post.

- Export public key `gpg --export <public key> > pub`
- Copy to server
- Import `gpg --import pub`
- Set trust `gpg --edit-key <public key>`, trust, 5, save
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

On Mac `brew install gnu-getopt pinentry-mac`

# sshfs Mac

From [this GitHub issue](https://github.com/telepresenceio/telepresence/issues/1654#issuecomment-873538291)

```sh
brew install --cask macfuse
brew install gromgit/fuse/sshfs-mac
brew link --overwrite sshfs-mac
```

# AMDGPU

### Backlight
```
ACTION=="add", SUBSYSTEM=="backlight", KERNEL=="acpi_video0", GROUP="video", MODE="0664"
RUN+="/bin/chgrp video /sys/class/backlight/acpi_video0/brightness"
RUN+="/bin/chmod g+w /sys/class/backlight/acpi_video0/brightness"
```

### Clocks
```
# Memory
/sys/class/drm/card0/device/hwmon/hwmon7/freq1_input
# GPU
/sys/class/drm/card0/device/hwmon/hwmon7/freq2_input
```
