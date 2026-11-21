#!/usr/bin/env python3
# Copyright (c) The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or https://opensource.org/license/mit/.

import re
import subprocess
import sys
import shlex


def run(cmd, **kwargs):
    print("+ " + shlex.join(cmd), flush=True)
    kwargs.setdefault("check", True)
    try:
        return subprocess.run(cmd, **kwargs)
    except Exception as e:
        sys.exit(str(e))


def main():
    print("Running tests on commit ...")
    run(["git", "log", "-1"])

    num_procs = int(run(["nproc"], stdout=subprocess.PIPE).stdout)
    build_dir = "ci_build"

    cmake_version_output = run(["cmake", "--version"], stdout=subprocess.PIPE, text=True).stdout
    cmake_version = re.search(r"cmake version (\\d+)\\.(\\d+)", cmake_version_output)
    cmake_args = [
        "cmake",
        "-B",
        build_dir,
        "-Werror=dev",
        "-DCMAKE_C_COMPILER=clang",
        "-DCMAKE_CXX_COMPILER=clang++",
        "-DCMAKE_EXE_LINKER_FLAGS=-fuse-ld=mold",
        "-DAPPEND_CXXFLAGS='-O3 -g2'",
        "-DAPPEND_CFLAGS='-O3 -g2'",
        "-DCMAKE_BUILD_TYPE=Debug",
        "-DCMAKE_COMPILE_WARNING_AS_ERROR=ON",
        "--preset=dev-mode",
        "-DCMAKE_CXX_FLAGS=-Wno-error=unused-member-function -Wno-error=unused-function",
    ]
    if cmake_version and (int(cmake_version.group(1)), int(cmake_version.group(2))) >= (4, 2):
        cmake_args.append("-Wno-error=non-target-directive")
    run(cmake_args)

    if run(["cmake", "--build", build_dir, "-j", str(num_procs)], check=False).returncode != 0:
        print("Build failure. Verbose build follows.")
        run(["cmake", "--build", build_dir, "-j1", "--verbose"])

    run([
        "ctest",
        "--output-on-failure",
        "--stop-on-failure",
        "--test-dir",
        build_dir,
        "-j",
        str(num_procs),
    ])
    run([
        sys.executable,
        f"./{build_dir}/test/functional/test_runner.py",
        "-j",
        str(num_procs * 2),
        "--failfast",
        "--combinedlogslen=99999999",
    ])


if __name__ == "__main__":
    main()
