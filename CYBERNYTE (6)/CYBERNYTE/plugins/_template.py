"""Copy this file, remove the leading underscore, and customize it."""

from rich.prompt import Prompt

# Choose one unused LETTER. Core CYBERNYTE currently uses D.
PLUGIN_KEY = "B"
PLUGIN_NAME = "My custom tool"


def run(console):
    """CYBERNYTE calls this function when your menu key is selected."""
    console.rule("[bold #ff5a00]My Custom Tool")
    name = Prompt.ask("What is your name?", default="Analyst")
    console.print(f"[green]Hello, {name}! Your plug-in is working.[/]")

