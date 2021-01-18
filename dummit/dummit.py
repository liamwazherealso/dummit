import click
import yaml
import os

@click.group()
def main():
    global __DBYAML__
    global strands
    __DBYAML__ = "strands.yml"
    with open(__DBYAML__, 'rb') as f:
        strands = yaml.load(f, Loader=yaml.FullLoader)

@click.command()
@click.argument('conf', required=True, type=click.File('rb'))
@click.argument('dockerfile', required=False, type=click.File('w'))
@click.option('--dry-run', is_flag=True, help="Print dockerfile")
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

    if "base" in strands:
        contents += "ARG BASE_IMAGE={}\n".format(strands["base"])
        contents += "FROM $BASE_IMAGE\n" 
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
