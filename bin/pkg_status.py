#!/usr/bin/env spack-python

from spack.spec import Spec
import spack.store
import spack.cmd

def main(argv):
    usage = f"Usage: {argv[0]} <spec> ... : <compiler> ..."
    assert len(argv) >= 4, usage
    argv = argv[1:]
    try:
        idx = argv.index(':')
    except ValueError:
        print(usage)
        exit(1)

    specs = argv[:idx]
    compilers = argv[idx+1:]

    stat_display = {False: '0', True: '1'}
    for spec in specs:
        result = spack.store.db.query(Spec(spec), known=True, installed=True)
        #spack.cmd.display_specs(result)
        print(' '.join(stat_display[any(s.satisfies(c) for s in result)] \
                                for c in compilers))

if __name__=="__main__":
    import sys
    main(sys.argv)
