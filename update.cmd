nssm stop NaotaBot
git pull
pyinstaller -F main.py
nssm start NaotaBot