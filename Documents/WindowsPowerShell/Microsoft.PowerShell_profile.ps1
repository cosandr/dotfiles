# Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser
# if (!(Test-Path -Path $PROFILE )) { New-Item -Type File -Path $PROFILE -Force }

# PSReadLine
Import-Module PSReadLine
Set-PSReadLineOption -EditMode Emacs
Set-PSReadlineKeyHandler -Key UpArrow -Function HistorySearchBackward
Set-PSReadlineKeyHandler –Key DownArrow -Function HistorySearchForward

Set-PSReadlineKeyHandler –Key Ctrl+RightArrow -Function ForwardWord
Set-PSReadlineKeyHandler –Key Ctrl+LeftArrow -Function BackwardWord

# Chocolatey profile
$ChocolateyProfile = "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
if (Test-Path($ChocolateyProfile)) {
  Import-Module "$ChocolateyProfile"
}

$HOSTS = "C:\Windows\System32\drivers\etc\hosts"
$env:EDITOR="vim"

function touch ($file) { Write-Output "" >> "$file" }
function la { Get-ChildItem -Force $args }
function ll { Get-ChildItem $args }
function sudoedit { Start-Process -Verb runAs vim $args }
function sudo-wt { Start-Process -Verb runAs wt.exe $args }
function rm-rf { Remove-Item -Recurse -Force $args }
function st { Start-Process "C:\Program Files\Sublime Text 3\sublime_text.exe" $args }
function cd-chezmoi { Set-Location $(chezmoi source-path) }
function reboot { Restart-Computer -Confirm }
function poweroff { Stop-Computer -Confirm }

function which {
    $c = Get-Command $args
    if ($c.CommandType -eq "Application") {
        $c.Source
    } elseif ($c.CommandType -eq "Function") {
        $c.ScriptBlock
    } else {
        $c
    }
}

function Set-Dev {
    Import-Module "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\Microsoft.VisualStudio.DevShell.dll";
    Enter-VsDevShell -SkipAutomaticLocation 1291dbd5
}
