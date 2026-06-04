import typer

from paper_insight.cli.chat import chat as chat_function
from paper_insight.cli.convert import app as convert_app
from paper_insight.cli.review import app as review_app

cli = typer.Typer(
    name="paper-insight",
    add_completion=False,
    help="AI-driven scientific paper screening and value assessment.",
)

cli.add_typer(convert_app, name="convert")
cli.add_typer(review_app, name="review")

@cli.command(help="Chat with the configured LLM model.")
def chat():
    """Interactive chat with the configured model."""
    chat_function()

if __name__ == "__main__":
    cli()
