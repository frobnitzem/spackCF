# example log
# indent levels are 2, 6, 10, 14, ...
# which can be parsed as (n-2)//4 -> 0, 1, 2, 3, ...
"""
==> Concretized hdf5%gcc@10.3.0
[+]  qc7rvqa  hdf5@1.10.7%gcc@10.3.0~cxx~fortran~hl~ipo~java+mpi+shared~szip~threadsafe+tools api=default build_type=RelWithDebInfo arch=cray-sles15-zen2
[+]  dmp6735      ^cmake@3.21.3%gcc@10.3.0~doc+ncurses+openssl+ownlibs~qt build_type=Release arch=cray-sles15-zen2
[+]  qt3s3ah          ^ncurses@6.2%gcc@10.3.0~symlinks+termlib abi=none arch=cray-sles15-zen2
[+]  ernqbep              ^pkgconf@1.8.0%gcc@10.3.0 arch=cray-sles15-zen2
[+]  bddeqeg          ^openssl@1.1.1l%gcc@10.3.0~docs certs=system arch=cray-sles15-zen2
[+]  esmiyhs              ^perl@5.34.0%gcc@10.3.0+cpanm+shared+threads arch=cray-sles15-zen2
[+]  2tfs2md                  ^berkeley-db@6.2.32%gcc@10.3.0+cxx~docs+stl patches=b231fcc4d5cff05e5c3a4814f6a5af0e9a966428dc2176540d2c05aff41de522 arch=cray-sles15-zen2
[+]  hshh7kt                  ^bzip2@1.0.8%gcc@10.3.0~debug~pic+shared arch=cray-sles15-zen2
[+]  joxjdx7                      ^diffutils@3.8%gcc@10.3.0 arch=cray-sles15-zen2
[+]  yvs3qro                          ^libiconv@1.16%gcc@10.3.0 libs=shared,static arch=cray-sles15-zen2
[+]  myyxrkk                  ^gdbm@1.19%gcc@10.3.0 arch=cray-sles15-zen2
[+]  uasrzdq                      ^readline@8.1%gcc@10.3.0 arch=cray-sles15-zen2
[+]  2gmti56                  ^zlib@1.2.11%gcc@10.3.0+optimize+pic+shared arch=cray-sles15-zen2
[+]  u3okiyl      ^cray-mpich@8.1.8%gcc@10.3.0 arch=cray-sles15-zen2

==> Concretized hdf5%gcc@10.3.0
[+]  qc7rvqa  hdf5@1.10.7%gcc@10.3.0~cxx~fortran~hl~ipo~java+mpi+shared~szip~threadsafe+tools api=default build_type=RelWithDebInfo arch=cray-sles15-zen2
[+]  dmp6735      ^cmake@3.21.3%gcc@10.3.0~doc+ncurses+openssl+ownlibs~qt build_type=Release arch=cray-sles15-zen2
[+]  qt3s3ah          ^ncurses@6.2%gcc@10.3.0~symlinks+termlib abi=none arch=cray-sles15-zen2
"""

from typing import List
from pathlib import Path

from text import Text

def parse_concretize(f : Text):
    """Returns a package digraph. Every node has a unique name like '<pkg>-<version>-<hash>' (where hash is only 7 chars).

    Input:
      f : Text iterator over lines

    Returns:
      (spec, G, roots).

    `spec` maps node names to spack specs.
    `G` maps node names to parents in the graph (explaining why something
    was compiled).
    `roots` maps node names to root specs which generated them. 
    """
    roots = {}
    specs = {}
    G = {}
    state = 0
    parent = [] # stack of parents
    root_spec = None
    for line in f:
        if len(line.strip()) == 0:
            state = 0
            continue
        v = line.startswith("==> Concretized ")
        if v:
            root_spec = v
            state = 1
            continue
        if state > 0:
            H, spec = line[5:].split(maxsplit=1)
            if spec[0] == '^':
                spec = spec[1:].strip()
            else:
                spec = spec.strip()
            name, t = spec.split('@', maxsplit=1)
            version, _ = t.split('%', maxsplit=1)
            node = f'{name}-{version}-{H[:7]}'

            specs[node] = spec
            if node not in G:
                G[node] = []
            if state == 1: # first line is special
                parent = [node]
                roots[node] = root_spec
                state = 2
                continue

            # indent level:
            n = line[5+7+2:].index('^') // 4
            assert n > 0, "Invalid indent level in concretize output"
            parent = parent[:n]
            parent.append(node)
            G[node].append(parent[n-1])

    return specs, G, roots

def find_roots(pkg, G):
    """Find all root packages that the pkg depends on.
    """
    visited = set()
    todo = [pkg]
    roots = []
    while len(todo) > 0:
        v = todo.pop()
        if v in visited:
            continue
        visited.add(v)
        if len(G[v]) == 0:
            roots.append(v)
        else:
            todo.extend(G[v])
    return roots

def explain_roots(errset, specs, G, roots):
    """ Return a mapping from a root-specs to the list of packages
    inside errset that the spec transitively depends on.
    """
    expl = {}
    for e in errset:
        for rname in find_roots(e, G):
            r = roots[rname]
            if r not in expl:
                expl[r] = []
            expl[r].append(e)
    return expl

def append_errs(base : Path, errset : List[str], out : Path) -> None:
    with open(base / 'concretize.log', encoding='utf-8') as f:
        specs, G, roots = parse_concretize( Text(f) )
    #roots = {rename_root(k):v for k,v in roots.items()}

    expl = explain_roots(errset, specs, G, roots)
    with open(out, 'a', encoding='utf-8') as f:
        f.write(f'\n# Build Issues\n\n')
        for root, deps in expl.items():
            f.write(f'* {root}\n')
            for dep in deps:
                f.write(f'    - [{specs[dep]}](issues/{dep})\n')
            f.write('\n')
