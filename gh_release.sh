source deactivate
source activate db
formatar_db --up_stel --up_radcom --up_mosaico dados
scp dados/VersionFile.json .
git add VersionFile.json
git commit -m ":bookmark: Release $(cat ./dados/.version)"
git push
gh release create $(cat ./dados/.version) dados/*.xlsx --generate-notes