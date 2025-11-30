"""Command-line interface for PDF2JSON."""

import click
from pathlib import Path
from .converter import PDFToXMLConverter


@click.command()
@click.argument("pdf_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output JSON file path (default: same as input with .json extension)"
)
@click.option(
    "--include-metadata",
    is_flag=True,
    help="Include PDF metadata in XML output"
)
@click.option(
    "--extract-tables",
    is_flag=True,
    help="Detect and extract tables from PDF"
)
@click.option(
    "--no-pretty",
    is_flag=True,
    help="Disable pretty-printing of XML"
)
def main(pdf_file: str, output: str, include_metadata: bool, extract_tables: bool, no_pretty: bool):
    """Convert PDF to JSON format."""
    try:
        if not output:
            output = Path(pdf_file).with_suffix(".json")
        
        click.echo(f"Converting {pdf_file} to JSON...")
        
        with PDFToXMLConverter(pdf_file) as converter:
            converter.save_json(
                output,
                include_metadata=include_metadata,
                extract_tables=extract_tables,
                indent=2 if not no_pretty else None
            )
        
        click.echo(f"✓ Successfully saved to {output}")
        
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error converting PDF: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
