rm -rf build
rm -rf ../docs
sphinx-build -b html source build
cp -r build ../docs
rm -rf build
cp .nojekyll ../docs/.nojekyll