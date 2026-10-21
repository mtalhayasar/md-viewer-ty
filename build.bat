@echo off
rem MD Viewer TY yayın derlemesi: exe + kurulum + taşınabilir zip + SHA256SUMS -> dist\
python -m pip install -r requirements-build.txt || exit /b 1
python tools\build.py %*
