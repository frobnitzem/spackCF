#!/bin/bash

if [[ $BASH_SOURCE = */* ]]; then
    SpackCFBASE=${BASH_SOURCE%/*}/..
else
    SpackCFBASE='..'
fi
cd $SpackCFBASE
SpackCFBASE=`pwd`

# download / update spack
if [ ! -d spack ]; then
    git clone --branch develop --depth 1 https://github.com/spack/spack spack
fi
export SPACK_DISABLE_LOCAL_CONFIG=1
export SPACK_USER_CACHE_PATH=$SpackCFBASE/home
export HOME=$SpackCFBASE/home
mkdir -p $HOME
source spack/share/spack/setup-env.sh

install_clingo() {
    module load PrgEnv-gnu
    module load cmake
    WD="$PWD"
    mkdir build; cd build
    curl -L -O https://github.com/potassco/clingo/archive/v5.5.0.tar.gz
    tar xzf v5.5.0.tar.gz
    mkdir clingo-5.5.0/build
    cd clingo-5.5.0/build
    cmake "-DCMAKE_INSTALL_PREFIX=$WD/venv" ..
    make -j8 install
    cd "$WD"
    rm -fr build
}

#if [ ! -d venv ]; then
if ! true; then
    module load cray-python/3.9.4.2
    python3 -m venv $SpackCFBASE/venv
    . venv/bin/activate
    install_clingo

    pip install clingo
    pip install cffi
    pip install pyyaml
    deactivate
fi

spack bootstrap root $SpackCFBASE/home/bootstrap
spack external find
