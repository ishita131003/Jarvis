$ws = New-Object -ComObject WScript.Shell
$desktop = [System.Environment]::GetFolderPath('Desktop')
$shortcut = $ws.CreateShortcut($desktop + '\Jarvis.lnk')
$shortcut.TargetPath = 'd:\rbu\BERAM\Jarvis\start_jarvis.bat'
$shortcut.IconLocation = 'd:\rbu\BERAM\Jarvis\assets\jarvis.ico'
$shortcut.WorkingDirectory = 'd:\rbu\BERAM\Jarvis'
$shortcut.Description = 'Jarvis AI Assistant'
$shortcut.Save()
Write-Host 'Shortcut created on Desktop!'
