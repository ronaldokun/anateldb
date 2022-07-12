# cd /c/users/rsilva/anateldb
# git pull
# source deactivate
# source activate db
# formatar_db --up_stel --up_radcom --up_mosaico dados
scp dados/VersionFile.json .
gh release create $(cat ./dados/.version) dados/*.xlsx --generate-notes
git add -A
git commit -m ":bookmark: Released $(cat ./dados/.version)"
git push