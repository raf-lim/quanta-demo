#!/bin/sh

if [ "${BUILD_ENV=prod}" = "dev" ]; then
    if [ ! -d backtests/files_repo ]; then
        mkdir files_repo
    fi
    if [ ! -d backtests/files_output ]; then
        mkdir files_output
    fi
    exec sh
fi