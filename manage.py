#!/usr/bin/env python3
import click
import os
import sys
from importlib import import_module, util
from pathlib import Path

COMMANDS_DIR = Path(__file__).parent / "app" / "management" / "commands"

def load_command_modules():
    """Dynamically load all command modules from the commands directory."""
    commands = {}
    for file in COMMANDS_DIR.glob("*.py"):
        if file.stem.startswith("_"):
            continue
        
        module_path = f"app.management.commands.{file.stem}"
        try:
            module = import_module(module_path)
            if hasattr(module, "cli") and isinstance(module.cli, click.Command):
                commands[file.stem] = module.cli
        except Exception as e:
            print(f"Warning: Failed to load command {file.stem}: {e}", file=sys.stderr)
    return commands

@click.group()
def cli():
    """Vault Integration management CLI."""
    pass

def main():
    # Add all commands to the CLI group
    commands = load_command_modules()
    for name, command in commands.items():
        cli.add_command(command, name=name.replace("_", "-"))
    
    cli()

if __name__ == "__main__":
    main()
