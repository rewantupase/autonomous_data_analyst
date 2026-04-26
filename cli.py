#!/usr/bin/env python3
"""
Autonomous Data Analyst — CLI
Usage: python cli.py
       python cli.py --provider anthropic
       python cli.py --question "Top 5 products by revenue"
"""
import os
import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from rich import box

console = Console()

BANNER = """[bold cyan]
  ██████╗  █████╗ ████████╗ █████╗      █████╗ ███╗  ██╗ █████╗ ██╗  ██╗   ██╗███████╗████████╗
  ██   ██╗██   ██╗   ██╔══╝██   ██╗    ██   ██╗████╗ ██║██   ██╗██║  ╚██╗ ██╔╝██╔════╝╚══██╔══╝
  ██   ██║███████║   ██║   ███████║    ███████║██╔██╗██║███████║██║   ╚████╔╝ ███████╗   ██║
  ██   ██║██   ██║   ██║   ██   ██║    ██   ██║██║╚████║██   ██║██║    ╚██╔╝  ╚════██║   ██║
  ██████╔╝██   ██║   ██║   ██   ██║    ██   ██║██║ ╚███║██   ██║███████╗██║   ███████║   ██║
  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝  ╚═╝╚═╝  ╚══╝╚═╝  ╚═╝╚══════╝╚═╝   ╚══════╝   ╚═╝
[/bold cyan]"""

SAMPLE_QUESTIONS = [
    "What are the top 5 products by total revenue?",
    "Show me monthly revenue trend for 2023",
    "Which customer region has the highest average order value?",
    "What is the correlation between customer age and spending?",
    "Show me the distribution of order sizes",
    "Which product categories are most profitable (revenue minus cost)?",
]


@click.command()
@click.option("--provider", default=None, help="LLM provider: openai or anthropic")
@click.option("--question", "-q", default=None, help="Run a single question non-interactively")
@click.option("--seed-db", is_flag=True, default=False, help="Seed the sample database first")
def main(provider, question, seed_db):
    if seed_db:
        console.print("[yellow]Seeding sample database...[/yellow]")
        from db.seed import seed
        seed()

    if provider:
        os.environ["LLM_PROVIDER"] = provider

    console.print(BANNER)
    console.print(Panel(
        f"[dim]LLM:[/dim] [cyan]{os.getenv('LLM_PROVIDER', 'openai').upper()}[/cyan]   "
        f"[dim]DB:[/dim] [cyan]{os.getenv('DATABASE_URL', 'sqlite:///./db/sample.db')}[/cyan]",
        title="[bold]Autonomous Data Analyst[/bold]",
        border_style="cyan",
    ))

    try:
        from agent import DataAnalystAgent
        agent = DataAnalystAgent()
    except EnvironmentError as e:
        console.print(f"[bold red]Config error:[/bold red] {e}")
        console.print("[dim]Copy .env.example → .env and fill in your API key.[/dim]")
        sys.exit(1)

    if question:
        _run_question(agent, question)
        return

    # Interactive loop
    console.print("\n[dim]Type a question, 'examples' to see samples, or 'quit' to exit.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]>[/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break
        if user_input.lower() == "examples":
            _show_examples()
            continue
        if user_input.lower().startswith("switch "):
            prov = user_input.split(" ", 1)[1].strip()
            try:
                agent.switch_provider(prov)
                console.print(f"[green]Switched to {prov.upper()}[/green]")
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
            continue

        _run_question(agent, user_input)


def _run_question(agent, question: str):
    from rich.spinner import Spinner
    from rich.live import Live

    console.print()
    with Live(console=console, refresh_per_second=10) as live:
        live.update(f"[cyan]⠸[/cyan] [dim]Thinking...[/dim]")
        result = agent.run(question)

    if result.error:
        console.print(Panel(f"[red]{result.error}[/red]", title="Error", border_style="red"))
        return

    # Summary
    console.print(Panel(
        Markdown(result.summary),
        title="[bold green]Answer[/bold green]",
        border_style="green",
    ))

    # SQL queries used
    if result.sql_queries:
        console.print(f"\n[dim]SQL queries executed ({len(result.sql_queries)}):[/dim]")
        for i, q in enumerate(result.sql_queries, 1):
            console.print(Panel(q.strip(), title=f"SQL #{i}", border_style="dim"))

    # DataFrames
    if result.dataframes:
        df = result.dataframes[-1]  # show last
        if not df.empty:
            table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
            for col in df.columns[:8]:
                table.add_column(str(col), overflow="fold")
            for _, row in df.head(10).iterrows():
                table.add_row(*[str(round(v, 2) if isinstance(v, float) else v) for v in row[:8]])
            console.print("\n[dim]Data preview:[/dim]")
            console.print(table)

    # Charts
    if result.chart_paths:
        console.print(f"\n[green]Charts saved:[/green]")
        for p in result.chart_paths:
            console.print(f"  [cyan]{p}[/cyan]")
    console.print()


def _show_examples():
    console.print("\n[bold]Sample questions:[/bold]")
    for i, q in enumerate(SAMPLE_QUESTIONS, 1):
        console.print(f"  [dim]{i}.[/dim] {q}")
    console.print()


if __name__ == "__main__":
    main()
