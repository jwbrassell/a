# Vault Management Script for Windows
# Must be run as Administrator for most operations

# Configuration
$VAULT_CONFIG_DIR = "C:\HashiCorp\Vault"
$VAULT_DATA_DIR = "vault-data"
$VAULT_LOG_FILE = "logs\vault.log"
$VAULT_AUDIT_FILE = "logs\vault-audit.log"
$CERT_DIR = "instance\certs"

# Check if running as Administrator
function Test-Administrator {
    $user = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($user)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Create necessary directories
function Create-Directories {
    Write-Host "Creating necessary directories..." -ForegroundColor Yellow
    
    New-Item -ItemType Directory -Force -Path $VAULT_CONFIG_DIR | Out-Null
    New-Item -ItemType Directory -Force -Path $VAULT_DATA_DIR | Out-Null
    New-Item -ItemType Directory -Force -Path "logs" | Out-Null
    New-Item -ItemType Directory -Force -Path $CERT_DIR | Out-Null
    
    Write-Host "Directories created" -ForegroundColor Green
}

# Initialize Vault
function Initialize-VaultServer {
    Write-Host "Initializing Vault..." -ForegroundColor Yellow
    
    $result = vault operator init -key-shares=1 -key-threshold=1 -format=json | ConvertFrom-Json
    
    # Save credentials
    $token = $result.root_token
    $unsealKey = $result.unseal_keys_b64[0]
    
    "VAULT_TOKEN=$token" | Out-File -FilePath ".env.vault"
    "VAULT_UNSEAL_KEY=$unsealKey" | Out-File -FilePath ".env.vault" -Append
    
    Write-Host "Vault initialized. Credentials saved to .env.vault" -ForegroundColor Green
}

# Start Vault
function Start-VaultServer {
    Write-Host "Starting Vault..." -ForegroundColor Yellow
    
    $process = Start-Process -FilePath "vault" -ArgumentList "server", "-config=config\vault-dev.hcl" -RedirectStandardOutput $VAULT_LOG_FILE -RedirectStandardError $VAULT_LOG_FILE -PassThru -WindowStyle Hidden
    
    Write-Host "Vault started (PID: $($process.Id))" -ForegroundColor Green
}

# Stop Vault
function Stop-VaultServer {
    Write-Host "Stopping Vault..." -ForegroundColor Yellow
    
    Get-Process | Where-Object { $_.ProcessName -eq "vault" } | Stop-Process -Force
    
    Write-Host "Vault stopped" -ForegroundColor Green
}

# Check Vault status
function Get-VaultStatus {
    Write-Host "Checking Vault status..." -ForegroundColor Yellow
    vault status
}

# Enable audit logging
function Enable-VaultAudit {
    Write-Host "Enabling audit logging..." -ForegroundColor Yellow
    vault audit enable file file_path="$VAULT_AUDIT_FILE"
    Write-Host "Audit logging enabled" -ForegroundColor Green
}

# Unseal Vault
function Unseal-Vault {
    if (Test-Path ".env.vault") {
        $envContent = Get-Content ".env.vault"
        $unsealKey = ($envContent | Where-Object { $_ -match "VAULT_UNSEAL_KEY=" }).Split("=")[1]
        
        Write-Host "Unsealing Vault..." -ForegroundColor Yellow
        vault operator unseal $unsealKey
        Write-Host "Vault unsealed" -ForegroundColor Green
    }
    else {
        Write-Host "No .env.vault file found" -ForegroundColor Red
        exit 1
    }
}

# Clean up Vault data
function Clear-VaultData {
    Write-Host "Cleaning up Vault data..." -ForegroundColor Yellow
    
    Stop-VaultServer
    
    Remove-Item -Path "$VAULT_DATA_DIR\*" -Force -Recurse
    Remove-Item -Path $VAULT_LOG_FILE -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $VAULT_AUDIT_FILE -Force -ErrorAction SilentlyContinue
    
    Write-Host "Cleanup complete" -ForegroundColor Green
}

# Show help
function Show-Help {
    Write-Host "Vault Management Script"
    Write-Host
    Write-Host "Usage: .\vault_manage.ps1 [command]"
    Write-Host
    Write-Host "Commands:"
    Write-Host "  start       Start Vault server"
    Write-Host "  stop        Stop Vault server"
    Write-Host "  status      Show Vault status"
    Write-Host "  init        Initialize Vault"
    Write-Host "  unseal      Unseal Vault"
    Write-Host "  audit       Enable audit logging"
    Write-Host "  cleanup     Clean up Vault data"
    Write-Host "  help        Show this help message"
}

# Main script logic
if ($args.Count -eq 0) {
    Show-Help
    exit 1
}

$command = $args[0]

# Check for admin rights except for status and help
if (-not (Test-Administrator) -and $command -notin @("status", "help")) {
    Write-Host "This script must be run as Administrator for most operations" -ForegroundColor Red
    exit 1
}

switch ($command) {
    "start" {
        Create-Directories
        Start-VaultServer
    }
    "stop" {
        Stop-VaultServer
    }
    "status" {
        Get-VaultStatus
    }
    "init" {
        Initialize-VaultServer
    }
    "unseal" {
        Unseal-Vault
    }
    "audit" {
        Enable-VaultAudit
    }
    "cleanup" {
        Clear-VaultData
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: $command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
