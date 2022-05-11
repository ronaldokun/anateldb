source deactivate
source activate db
formatar_db dados --up_stel true --up_radcom true --up_mosaico true
scp dados/VersionFile.json .
git add VersionFile.json
git commit -m ":bookmark: Release $(cat ./dados/.version)"
git push
gh release create $(cat ./dados/.version) dados/*.xlsx --generate-notes