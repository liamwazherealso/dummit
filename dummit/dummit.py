import click
import docker
import yaml


def hadolint(dockerfile):
    client = docker.from_env()
    client.containers.run("hadolint/hadolint", "< {}".format(dockerfile))


@click.group()
def main():
    global __DBYAML__
    global strands_db
    __DBYAML__ = "strands.yml"
    with open(__DBYAML__, "rb") as f:
        strands_db = yaml.load(f, Loader=yaml.FullLoader)


@click.command()
@click.argument("conf", required=True, type=click.File("rb"))
@click.argument(
    "dockerfile",
    required=False,
    type=click.File("w", encoding="ascii", errors="surrogateescape"),
)
@click.option("--dry-run", is_flag=True, help="Print dockerfile")
def generate(conf, dockerfile, dry_run):
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
        baseImage = "pytorch/pytorch:{}-cuda{}-cudnn7-devel".format(
            strands["pytorch"], strands["cuda"]
        )
        del strands["pytorch"]
        del strands["cuda"]

    contents += "ARG BASE_IMAGE={}\n".format(baseImage)
    contents += "FROM $BASE_IMAGE\n"

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


class MalformedConf(Exception):
    """Conf list item was not of the form `Dependency==Version`"""

    pass


main.add_command(generate)
if __name__ == "__main__":
    main()
