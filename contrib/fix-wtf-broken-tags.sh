#!/bin/sh -
# re-adds all the tags that are all.. weird. so they are no longer.. weird.
printf "don't just run this without looking at what it does\n" 1>&2
tput bel
exit 255

set -ef +xva --

head="$(git rev-parse HEAD)"
git for-each-ref refs/tags | \
	while read -r hash type refname
	do
		if test x"$type" = xcommit
		then
			tag="${refname#refs/tags/}"
			if test x"$hash" = x"$(git rev-parse "$tag")"
			then
				realhash="$(git merge-base "$hash" "$head")"
				if test x"$realhash" != x"$hash"
				then
					printf "%s -> %s\n" "$(git name-rev "$realhash")" "$tag" 1>&2
					IFS="" read -r author <<-__SHOW__
					$(git show -s --date=raw --pretty=tformat:"%an <%ae> %ad" "$realhash")
					__SHOW__
					tagid="$(
						git mktag <<-__TAG__
						object $realhash
						type commit
						tag $tag
						tagger $author
						
						release $tag
						__TAG__
					)"
					if test x"$tagid" = x
					then
						printf "failed to create tag somehow..\n" 1>&2
						exit 1
					fi
					git tag -d "$tag" && \
						git update-ref refs/tags/"$tag" "$tagid" ""
					printf "fixed tag: %s\n" "$tag"

				fi
			fi
		fi
	done

