#!/bin/bash

if [[ $BASH_SOURCE = */* ]]; then
    SpackCFBASE=${BASH_SOURCE%/*}/..
else
    SpackCFBASE='..'
fi
cd $SpackCFBASE
SpackCFBASE=`pwd`

if [ ! -x spack/share/spack/setup-env.sh ]; then
    echo "Incomplete install -- run install.sh first."
    exit 1
fi
export SPACK_DISABLE_LOCAL_CONFIG=1
export SPACK_USER_CACHE_PATH=$SpackCFBASE/home
export HOME=$SpackCFBASE/home
source spack/share/spack/setup-env.sh

MIRROR=$SpackCFBASE/mirror
[ -d $MIRROR ] || mkdir -p $MIRROR

config_name() {
    if [ ! -d builds/$out ]; then
        echo "No builds/$out. First run buildPlan."
        exit 1
    fi
    tail -n1 builds/$out/envname.txt
}
