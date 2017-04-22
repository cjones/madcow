#!/bin/sh -

set -euf

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH

for cmd in env sh make mkdir clang sed grep python brew id sysctl git autoreconf
do
	eval $cmd='"$(which "$cmd")"'
done

run () (set -x; "$@")
env () { run "$env" - PATH="$PATH" LANG=C LC_ALL=C SHELL="$sh" "$@"; }

srcdir="$(pwd)"
prefix="$(cd "$srcdir"/.. && pwd)"/python
build="$srcdir"/build
ncpu=$(env "$sysctl" -n hw.ncpu || true)

pyuniq='
import sys
s = set()
a, c, w = s.add, s.__contains__, sys.stdout.write
for l in sys.stdin:
 if not c(l): a(l), w(l)
'

_clean_config_opts ()
{
	env "$sed" -E 's/^[ ]{0,}//g' |
	env "$grep" -Ev '^--'
	env "$sed" -E 's/[[]{0,1}[=].*$//g' |
	env "$sed" -E 's/[ ].*$//g' |
	env "$sed" -E 's/with[(]out[)]/with/g' |
	env "$python" -c "$pyuniq" |
	env "$sed" -E 's/^/	/g' |
	env "$sed" -E 's/$/ \\/g'
}

_get_deps ()
{
	cppflags=""
	ldflags=""

	user="$(env "$id" -un)"
	eval home="~$user"

	brew () { env HOME="$home" "$brew" "$@"; }

	while read -r pkg
	do
		if test x"$pkg" != x
		then
			pkgdir="$(brew --prefix "$pkg" || true)"
			if test x"$pkgdir" != x && test -d "$pkgdir"
			then
				incdir="$pkgdir"/include
				! test -d "$incdir" || cppflags="${cppflags:+"$cppflags "}-I"$incdir""
				libdir="$pkgdir"/lib
				! test -d "$libdir" || ldflags="${ldflags:+"$ldflags "}-L"$libdir""
			fi
		fi
	done <<-__PKGS__
	$(
		brew deps --1 --full-name --installed --include-build --include-optional python3
	)
	__PKGS__
}

_get_deps

(
	cd "$srcdir" &&
	env "$git" reset --hard HEAD &&
	env "$git" clean -dxf &&
	env "$autoreconf" &&
	env "$mkdir" -p "$build" &&
	cd "$build" &&
	env "$sh" "$srcdir"/configure \
	--cache-file="$build"/config.cache \
	${srcdir:+--srcdir="$srcdir"} \
	${prefix:+--prefix="$prefix"} \
	--disable-universalsdk \
	--disable-framework \
	--disable-shared \
	--disable-profiling \
	--disable-optimizations \
	--enable-loadable-sqlite-extensions \
	--enable-ipv6 \
	--without-gcc \
	--without-suffix \
	--without-pydebug \
	--with-threads \
	--with-doc-strings \
	--without-valgrind \
	--without-dtrace \
	--with-ensurepip=install \
	CC="$clang" \
	CFLAGS="-O0 -pipe -Wno-unused-value -Wno-empty-body -Qunused-arguments" \
	${ldflags:+LDFLAGS="$ldflags"} \
	${cppflags:+CPPFLAGS="$cppflags"} \
	CPP="$clang -E" \
	PKG_CONFIG="$(which pkg-config)" &&
	env "$make" ${ncpu:+-j"$ncpu"} &&
	(if test x"$prefix" != x; then test -d "$prefix" || env "$mkdir" -p "$prefix"; fi) &&
	env "$make" install
)

exit $?
