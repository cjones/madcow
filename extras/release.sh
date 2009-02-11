# update __version__ in main bot
# diff trunk from previous release and update ChangeLog
# make a release tag:

release="madcow-1.5.4"

svn copy https://madcow.googlecode.com/svn/trunk https://madcow.googlecode.com/svn/tags/$release || exit

# export
svn export https://madcow.googlecode.com/svn/tags/$release

# remove extras
rm -rf ${release}/extras/

# make bundle
tar cfjv ${release}.tar.bz2 $release

# cleanup
rm -rf ${release}

echo "ready to release: ${release}.tar.bz2"

# upload to anon ftp
rsync -vPazue ssh ${release}.tar.bz2 cj__@frs.sourceforge.net:uploads/

echo "activate release at:"
echo "http://sourceforge.net/project/admin/editpackages.php?group_id=199970"


