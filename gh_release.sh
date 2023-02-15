scp dados/VersionFile.json .
git add -A
git commit -m ":bookmark: Released $(cat ./dados/.version)"
git push