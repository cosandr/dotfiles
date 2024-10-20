#!/usr/bin/env bash

# Only run on Mac
[[ $(uname -s) != "Darwin" ]] && exit 0

set -eu

# https://apple.stackexchange.com/a/470622
echo "Installing launch daemon plist"
sudo /usr/bin/env bash -c "cat > /Library/LaunchDaemons/org.custom.tilde-switch.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>org.custom.tilde-switch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/sudo</string>
        <string>${HOME}/.local/bin/tilde-switch</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
  </dict>
</plist>
EOF

echo "Load launch daemon"
sudo launchctl load -w -- /Library/LaunchDaemons/org.custom.tilde-switch.plist
