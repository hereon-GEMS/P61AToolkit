rmdir /s /q build
rmdir /s /q  ..\docs
mkdir ..\docs
sphinx-build -b html source build
Xcopy /i /r /q /E build\* ..\docs
rmdir /s /q build