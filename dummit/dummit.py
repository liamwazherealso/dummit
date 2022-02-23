import json
import subprocess
import sys
from typing import Any, List

import click
import yaml

FORE_RED = "\033[1;31m"
FORE_YELLOW = "\033[1;33m"
RESET_COLOR = "\033[m"

parsed_errors: List[Any]
color_setting: str


def should_use_colors():
    return color_setting == "always" or color_setting == "auto" and sys.stdout.isatty()


def style_error(e):
    error_msg = f'{e["code"]}: {e["message"]}'
    if should_use_colors():
        prefix = {
            "error": FORE_RED,
            "warning": FORE_YELLOW,
        }.get(e["level"], FORE_RED)
        suffix = RESET_COLOR
    else:
        prefix = {
            "error": "[x] ",
            "warning": "[!] ",
        }.get(e["level"], "[x] ")
        suffix = ""
    return f"{prefix}{error_msg}{suffix}"


def print_errors_if_any(lineno):
    line_errors = [e for e in parsed_errors if e["line"] == lineno]
    for e in line_errors:
        print(style_error(e))


strands_db = None
strands_path = None
strands = None


def hadolint(dockerfile):
    with open(dockerfile) as f:
        input_lines = f.read().splitlines()

    cmd = [
        "docker",
        "run",
        "--rm",
        "-i",
        "hadolint/hadolint",
        "hadolint",
        "--format",
        "json",
        "-",
    ]

    input_bytes = "\n".join(input_lines).encode()
    process = subprocess.run(
        cmd, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if len(process.stderr) > 0:
        print(process.stderr.decode(), file=sys.stderr)

    global parsed_errors
    if len(process.stdout) > 0:
        parsed_errors = json.loads(process.stdout)
        if len(parsed_errors) > 0:
            for n, line in enumerate(input_lines, start=1):
                print_errors_if_any(n)
                print(line)


@click.group()
def cli():
    pass


def load_strands_db(strands_path):
    with open(strands_path, "rb") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


@click.command()
@click.argument("conf", required=True, type=click.File("rb"))
@click.argument(
    "dockerfile",
    required=False,
    type=click.File("w", encoding="ascii", errors="surrogateescape"),
)
@click.option("--dry-run", is_flag=True, help="Print dockerfile")
@click.option("--strands-path", help="Path to strands yml", default="strands.yml")
@click.option("--color", type=click.Choice(["never", "auto", "always"]), default="auto")
def generate(conf, dockerfile, dry_run, strands_path, color):
    strands_db = load_strands_db(strands_path)

    global color_setting, parsed_errors
    color_setting = color

    conf = yaml.load(conf, Loader=yaml.FullLoader)
    contents = ""
    strands = {}

    # load conf
    for strand in conf:
        strand = strand.split("==")
        if len(strand) == 1:
            strand, val = strand[0], -1
        elif len(strand) == 2:
            strand, val = strand[0], strand[1]
        else:
            raise MalformedConf
        strands[strand] = val

    if "base" in conf:
        baseImage = conf["base"]
        del conf["base"]

    # Catch special cases
    if "pytorch" in strands and "cuda" in strands:
        baseImage = "pytorch/pytorch:{}-cuda{}-cudnn{}-{}".format(
            strands["pytorch"], strands["cuda"], strands["cudnn"], strands["mode"]
        )
        del strands["pytorch"]
        del strands["cuda"]
        del strands["cudnn"]
        del strands["mode"]

    contents += "FROM {}\n".format(baseImage)

    # Add remaining strands
    for strand, value in strands.items():
        if value == -1:
            contents += strands_db[strand]
        else:
            contents += strands_db[strand][value]

    if dry_run:
        print(contents)
    else:
        dockerfile.write(contents)
        dockerfile.close()
        hadolint(dockerfile.name)


class MalformedConf(Exception):
    """Conf list item was not of the form `Dependency==Version`"""

    pass


cli.add_command(generate)
if __name__ == "__main__":
    cli()
