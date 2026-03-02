export LIBDIR=/usr/lib/python3.12
export PYTHONLIBPATH=/usr/lib/python3.12
export PYTHONINCLUDEPATH=/usr/include/python3.12

echo "PYTHONLIBPATH: $PYTHONLIBPATH"
echo "PYTHONINCLUDEPATH: $PYTHONINCLUDEPATH"
echo "LIBDIR: $LIBDIR"

# On ubuntu: apt install -y libsndfile1 libsndfile1-dev
# Original from the repo: yum install -y libsndfile libsndfile-devel

echo "Build Nanobind"
cd third_party/nanobind
git submodule update --init --recursive
cmake -S . -B build -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake --build build
cd ../..

make headless_server

echo "build_linux.sh is done!"

# to build a wheel:
# python3 -m build --wheel