source activate db
formatar_db dados --up_stel --up_radcom --up_mosaico
git add -A && git commit -m ":bookmark: Base Atualizada" && git push
gh release create $(cat ./dados/.version) dados/*.xlsx --generate-notes