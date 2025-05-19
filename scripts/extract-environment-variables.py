#!/usr/bin/env python3

"""
Environment variable extractor.

Example Usage:

    python extract-environment-variables.py --env-file .env.example
    python extract-environment-variables.py --env-file .env.example --include-defaults

"""

import pprint
import string
import sys
import json
import re
import os
import pathlib
import logging
import argparse
import typing
import configparser

handler = logging.StreamHandler()

logger = logging.getLogger(__name__)

class Formatter(logging.Formatter):
    expression = r"(?<!\w)'([^\s']+)'(?!\w)"
    substitution = r'"\1"'

    def format(self, record) -> str:
        # Modify the record or format the message as needed.
        v = super().format(record)  # .replace("'", "%s" % '"')

        return re.sub(self.expression, self.substitution, v)

formatter = Formatter("[%(levelname)s] (%(asctime)s) (%(name)s) %(message)s")

handler.setFormatter(formatter)

def main():
    logging.basicConfig(level=logging.DEBUG, datefmt="%Y-%m-%dT%H:%M:%SZ")
    logger.addHandler(handler)
    logger.propagate = False

    # Create an argument parser object.
    parser = argparse.ArgumentParser(description="Extract environment variable(s)")

    parser.add_argument("-e", "--env-file", dest="file", type=str, metavar="FILE", help="the relative or full-system path", required=False, default=".env")
    parser.add_argument("-i", "--include-defaults", dest="include-defaults", action="store_true", help="include default environment variables in output")

    # Parse arguments.
    namespace = parser.parse_args()

    arguments = vars(namespace)

    logger.debug("Arguments: %r", arguments)

    file = pathlib.Path(arguments["file"]).resolve()

    logger.info("Target File: \"%s\"", file)

    if not file.exists():
        raise RuntimeError("Target file \"%s\" does not exist" % file)
    elif not file.is_file():
        raise RuntimeError("Target descriptor \"%s\" is not a file" % file)
    elif not os.access(file, os.R_OK):
        raise RuntimeError("Target file \"%s\" is not readable" % file)

    configuration = configparser.ConfigParser(allow_no_value=True, empty_lines_in_values=False, allow_unnamed_section=True)

    configuration.read(file)

    hashmap: dict[str, dict[str, str]] = {}
    for section in configuration.sections():
        for key, value in configuration.items(section):
            normalized = key.replace("_", "-")
            value = value.strip()

            # Use the current process' environment variables as a possible default.
            if len(value) == 0 and os.environ.get(key) is not None:
                value = os.environ.get(key)

            if normalized not in hashmap:
                hashmap[normalized] = {
                    "value":    value,
                    "variable": key.upper(),
                }

    partials: list[str] = [
        "cp .env.example .env",
        "",
        "function replace() {",
        "    sed -i \"s/${1}=.*/${1}=${2}/\" .env",
        "}",
        "",
        "# Secrets replacement(s) through actions configuration"
    ]

    secrets: list[str] = []
    defaults: list[str] = []

    for value in hashmap.values():
        secret: bool = True

        assignment = value["value"]
        variable = value["variable"]

        literal = "replace \"{0}\" \"${{{{ secrets.{0} }}}}\"".format(variable)
        if len(assignment) > 0:
            secret = False

            logger.debug("Found Default Configuration Value (%s): %s", variable, assignment)

            literal = "replace \"{0}\" \"{1}\"".format(variable, assignment)

        secrets.append(literal) if secret else defaults.append(literal)

    partials.extend(secrets)

    if arguments["include-defaults"]:
        partials.append("")
        partials.append("# Defaults configuration ")
        partials.append("")

        partials.extend(defaults)

    sys.stdout.write("\n%s\n\n" % "\n".join(partials))

if __name__ == "__main__":
    main()
