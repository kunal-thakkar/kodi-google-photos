mkdir plugin.picture.picasa4kodi
cp -r `ls | grep -v ".git" | grep -v "plugin.picture.picasa4kodi"` plugin.picture.picasa4kodi/
zip -r ../plugin.picture.picasa4kodi.zip plugin.picture.picasa4kodi/
rm -rf plugin.picture.picasa4kodi/