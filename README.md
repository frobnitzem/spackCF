# Spack for Compute Facilities

This package implements system integrations for
compiling an HPC center's software stack.

In general, HPC systems have a base layer of custom
libraries which serve a software stack built on top.
Both the base layer and the upper software stack
have ongoing, independent development efforts.
This leads to synchronization issues between the system
and user software that can be difficult to document
and work with consistently.

We provide system administration utilities allowing:

  * baseVer: detect changes in base system version info.

  * `buildPlan <config> <out>`: update current plan of environments to build 
    - comparing the effects of changes in spack to the build DAG

  * `buildStep <out>`: incrementally building packages with spack 
    - caching spack builds

  * `buildStat <out>`: check status of an ongoing/completed build

  * not run directly by user: 
    * env.sh: load spack's environment (helper script)

These utilities manipulate a filesystem hierarchy, consisting of
spack, base installations and environments:

    environments/      # version-controlled build setup directory
      gather.sh        # shell file creating a yaml representation of base info.
                       # (not yet used)
      <config>/
        env.sh         # shell-file used to setup environment variables/modules
                       # before calling spack (not yet implemented)
        spack.yaml     # full environment file
        pkg-list.yaml  # categorized list of target packages to report
        repo/          # repository for site-local modifications to package.py files
      ...
    ##### user-managed files #####
    spack/             # clone of the spack/spack repository
    ##### auto-generated files #####
    home/              # files that spack would normally keep in your $HOME
        cache/         # database of random facts spack maintains
        bootstrap/     # python virtual environment holding clingo
    mirror/            # source tarballs mirror
    base/
      <version>/       # output directory per base version
        version.yaml   # output of gather.sh
        install/       # spack install prefix path
        cache/         # spack build cache
      ...
    builds/            # build status info.
      <out>/           # output dir named by user
        config/        # full copy of <config> used to generate this build
        envname.txt    # name of spack environment file initially used
        concretize.log # log file from buildPlan's concretization step
        install.nnn.log # logfiles from runs of buildStep
        Makefile       # makefile output by spack env
                       # (used to download pkgs in buildPlan's last step)
        status.md      # build status output (output by buildStat)
        errors/        # detailed outputs of failing builds

Each base has an independent build-cache and install directory.
Each environment has a `spack.yaml` configuration and a repository.

# baseVer: Gather base system version info

Usage: baseVer

1. executes `base/gather.sh`
2. compares result to each of the version.yaml files in `base/`
3. creates a new directory if none match
4. checks that venv is installed correctly
5. prints out the resulting `base/<version>` path


# buildPlan:

Usage: `buildPlan <config> <out>`

1. loads virtual environment for the base OS
2. checks the environment against existing environments. If this patch of the environment is not present, does the following:
  - creates a new patch version
  - concretizes
3. [downloads sources](https://spack.readthedocs.io/en/latest/mirrors.html#mirror-environment) for all packages to the `mirror` directory
4. prints out a [DAG](https://spack.readthedocs.io/en/latest/packaging_guide.html#graphing-dependencies) of the packages to be built


# buildStep:

Usage: `buildStep <config>`

Run a parallel build worker for the given environment.
The build worker checks that the environment matches its spec,
and is concretized.  Then runs spack install, logging all results
to `builds/<out>/install.nnn.log`.


# buildStat:

Usage: `buildStat <out>`

Gathers build status information and outputs to `builds/<out>/status.md`
and `builds/<out>/errors.md`.


