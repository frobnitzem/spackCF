#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is released into the public domain by its authors.
#
import re
import yaml
from pathlib import Path
from typing import List
from subprocess import check_output, CalledProcessError

from parse_concretize import append_errs
from text import Text

# legend for package status summary table
legend = {
     "ok": "✅",
     "err": "❌",
     "warn": "⚠️",
     "na": "N/A",
   }
# related:
#    "rock": "🎵", # ♫
#    "flat": "♭" # no rest?
#    "rock": "🎸"

def parse_errors(text : Text, errors : dict):
    state = 0 # initial
    # state 1 = parsing pkg compile info
    # state 2 = parsing error
    pkg = None # current package
    message = [] # current error message

    def reset():
        nonlocal state, pkg, message, errors
        if state == 2:
            errors[pkg] = ''.join(message)
        state = 0
        pkg = None
        message = []

    for line in text:
        if line.startswith("[+]"):
            reset()
            continue
        v = line.startswith("==> Installing")
        if v is not None:
            reset()
            state = 1 # parsing an install process
            n = len(v.rsplit('-', 1)[0]) # location of last -
            pkg = v[:n+8] # truncate pkg name (matching concretize node name)
            continue
        if state == 1:
            v = line.startswith("==> Error:")
            if v is not None:
                message.append(v)
                state = 2
                continue
        if state == 2:
            message.append(line)

    reset()

def parse_stat():
    # Not currently used, no easy way to check specs for subtype
    # match against the (built) list returned here!
    from spack.spec import Spec
    # parse the output of spack find -x into
    # gcc and cce lists
    stat = check_output(["spack", "find", "-xv"], encoding='utf-8')

    builds = {'cce':set(), 'gcc':set(), 'cla':set()}
    cur = None
    for line in Text(stat.split('\n')):
        if line.startswith("-- cray-sles15-zen2 / "):
            cur = line.split()[3][:3] # cce and gcc
            continue
        elif line.startswith("--"):
            cur = None
            continue
        if len(line) == 0 or cur is None:
            continue
        print(f"adding spec {line} to {cur}")
        try:
            builds[cur].add( Spec(line) )
        except KeyError:
            pass

    builds['amd'] = builds['cla']
    del builds['cla']
    return builds

def parse_matrix(lines, rows, cols):
    decode = {'0': False, '1': True}
    M = []
    for line in lines:
        tok = line.split()
        if len(tok) != cols:
            continue
        M.append([decode[t] for t in tok])
    assert len(M) == rows, "Invalid output!"
    return M

def did_build(pkgs : List[str], compilers : List[str]):
    # Return a matrix of pkg x compilers 0-s and 1-s relating to
    # 1 = installed, 0 = not installed
    args = ['bin/pkg_status.py']+pkgs+[':']+compilers
    ans = check_output(args, encoding='utf-8')
    return parse_matrix(ans.split('\n'), len(pkgs), len(compilers))

def lookup_status(pkg_list : str, out : Path) -> None:
    # builds = parse_stat() # too cumbersome to match specs this way
    # TODO: search through `stat` for each package
    # and link to errors/ txt file for explanation!
    pkgs = yaml.safe_load(open(pkg_list))

    compilers = ["Cray", "CrayCC", "GCC", "AMD"]
    compiler_specs = ['%cce@13.0.2', '%cce@13.0.2-lite', '%gcc', '%rocmcc']
    assert len(compilers) == len(compiler_specs)
    cols = ["spec"] + compilers
    # write a markdown-table header
    def write_hdr(f):
        f.write("| " + " | ".join(cols) + " |\n")
        f.write("| " + " | ".join("-"*len(c) for c in cols) + " |\n")

    stat = { True: legend["ok"],
             False: legend["err"]
           }

    with open(out, 'w', encoding='utf-8') as f:
        f.write("# Package Status\n")
        for name,group in pkgs.items():
            f.write(f"\n## {name}\n")
            write_hdr(f)
            status = did_build(group, compiler_specs)
            # status is a listy-matrix (group x compiler_specs)
            for spec, pkg in zip(group, status):
                vals = [spec] + [stat[j] for j in pkg]
                f.write("| " + " | ".join(vals) + " |\n")

        #f.write("\nKey:\n")
        #for k,v in legend.items():
        #    f.write(f"* {k} {v}\n")
        return None

def rename_root(n):
    """ Rename package to (pkg,compiler)
    """
    m = re.match(r'([^%]*)%([^@]*)@([.0-9]*)', n)
    return (m[1] + n[m.end():], m[2])

def main(argv):
    assert len(argv) == 3, f"Usage: {argv[0]} <pkg-list.yaml> <base dir containing concretize.log and install.nnn.log>"
    base = Path(argv[2])
    outputs = list(base.glob('install.*.log'))
    outputs.sort()
    err = {}
    for log in outputs:
        with open(log, encoding='utf-8') as f:
            parse_errors( Text(f), err )

    out = base / 'errors'
    out.mkdir(exist_ok=True)
    for k, v in err.items():
        with open(out/k, 'w', encoding='utf-8') as f:
            f.write(v)
    print(f"{len(err)} build errors")
    errset = lookup_status(argv[1], base / 'status.md')
    append_errs(base, list(err.keys()), base / 'status.md')

if __name__=="__main__":
    import sys
    main( sys.argv )
