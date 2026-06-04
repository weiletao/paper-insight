import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

sys.path.append(str(Path(__file__).parent.parent.parent))

from paper_insight.config import Settings
from paper_insight.providers import create_provider

console = Console()


def chat():
    """Run interactive chat with the configured model."""
    try:
        # Load settings
        settings = Settings.from_yaml()

        # Validate model configuration
        if not settings.model.model_name:
            console.print("[red]Error: model_name is required in config.yaml[/red]")
            sys.exit(1)

        if not settings.model.api_key:
            console.print("[red]Error: api_key is required in config.yaml[/red]")
            sys.exit(1)

        # Create provider
        provider = create_provider(settings.model.model_dump())

        console.print(f"[bold green]Chat started with {settings.model.model_name}[/bold green]")
        console.print("Type 'quit' or 'exit' to end the chat\n")

        # Main chat loop
        while True:
            # Get user input
            user_input = console.input("[blue]You:[/blue] ")

            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not user_input.strip():
                continue

            # Generate response
            try:
                response = provider.generate(user_input)

                # Display response
                console.print("\n[bold green]Assistant:[/bold green]")
                console.print(response)
                console.print("\n")

            except Exception as e:
                console.print(f"\n[red]Error: {str(e)}[/red]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Chat interrupted. Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


app = chat