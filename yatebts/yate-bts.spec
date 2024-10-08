# to add a distro release tag run rpmbuild --define 'dist value'
# to add a revision tag run rpmbuild --define 'revision value'
# to create a debug info package run rpmbuild --define 'debuginfo 1'
# to suppress auto dependencies run rpmbuild --define 'nodeps 1'
# to build a standalone (not yate-sdr) package run rpmbuild --define 'nosdr 1'

%{!?dist:%define dist %{nil}}
%{!?revision:%define revision %{nil}}
%{!?_unitdir:%define _unitdir /usr/lib/systemd/system}
%{?nodeps:%define no_auto_deps 1}
%{!?nosdr:%define nosdr 0}

%if %{nosdr}
%define serv_name yate
%define cfgdir	/usr/local/etc/yate
%define xtra_stat nosdr.
%else
%define serv_name yate-sdr
%define cfgdir	%{_sysconfdir}/yate/sdr
%define xtra_stat %{nil}
%endif

%{!?debuginfo:%define debuginfo %{nil}}
%if "%{debuginfo}"
%define stripped debug
%else
%define stripped strip
%define debug_package ${nil}
%endif

%if "%{revision}" == "svn"
%define revision svn
%endif

%if "%{dist}" == ""
%define dist %{?distsuffix:%distsuffix}%{?product_version:%product_version}
%endif
%if "%{dist}" == ""
%define dist %(test -f /etc/mageia-release && echo mga)
%endif
%if "%{dist}" == ""
%define dist %(test -f /etc/mandriva-release && echo mdv)
%endif
%if "%{dist}" == ""
%define dist %(test -f /etc/mandrake-release && echo mdk)
%endif
%if "%{dist}" == ""
%define dist %(test -f /etc/fedora-release && echo fc)
%endif
%if "%{dist}" == ""
%define dist %(grep -q ^CentOS /etc/issue && echo centos)
%endif
%if "%{dist}" == ""
%define dist %(test -f /etc/redhat-release && echo rh)
%endif
%if "%{dist}" == ""
%define dist %(test -f /etc/SuSE-release && echo suse)
%endif
%if "%{dist}" == "none"
%define dist %{nil}
%endif

Summary:	GSM BTS based on Yet Another Telephony Engine
Name:		yate-bts
Version: 	6.1.1
Release:	%{xtra_stat}devel%{revision}1%{?status:_%{status}}%{dist}
License:	GPL
Packager:	Paul Chitescu <paulc@null.ro>
Source:		https://yatebts.com/%{name}-%{version}-devel1.tar.gz
Group:		Applications/Communication
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root
URL:		https://yatebts.com/
%{?extra_prov:Provides: %{?extra_prov}}
%{?extra_reqs:Requires: %{?extra_reqs}}
BuildRequires:	gcc-c++
BuildRequires:	yate-devel >= 6.1.0
Requires:	yate = 6.4.1
Requires:	yate-gsm = 6.4.1
Requires:	yate-radio = 6.4.1
%if %{nosdr}
Conflicts:	yate-enb
%else
Requires:	yate-sdr
%endif
Conflicts:	yate-bts-transceiver

%define prefix	/usr
%define moddir	%{_libdir}/yate/server
%define btsdir	%{moddir}/bts
%define shrdir	/usr/local/share/yate
%define scrdir	/usr/local/share/yate/scripts

%description
Yate is a telephony engine designed to implement PBX and IVR solutions
for small to large scale projects.
This module implements a 2G GSM BTS for Yate.
At least one Yate radio device package must also be installed.

%files
%defattr(-, root, root)
%docdir %{_defaultdocdir}/%{name}-%{version}
%doc %{_defaultdocdir}/%{name}-%{version}/*
%dir %{btsdir}
%{moddir}/*.yate
%{btsdir}/mbts
%if %{nosdr}
%config(noreplace) %{cfgdir}/ybts.conf
%else
%{shrdir}/api/*
%{scrdir}/bts_config.js
%{scrdir}/nipc_config.js
%{scrdir}/nipc_validations.js
%{scrdir}/ybts_fields.js
%{cfgdir}/bts-jscript.conf
%endif

%post
%if ! %{nosdr}
test "X$1" = "X1" && %{_datadir}/yate/scripts/rpm_restore.sh %{name}
%endif
if grep -q '^ *Radio.C0 *= *[0-9]' %{cfgdir}/ybts.conf 2>/dev/null; then
    if [ -s %{_unitdir}/%{serv_name}.service ]; then
        systemctl condrestart %{serv_name}.service
    else
        if [ -s /etc/init.d/%{serv_name} ]; then
            service %{serv_name} condrestart
        fi
    fi
fi

%postun
if [ -s %{_unitdir}/%{serv_name}.service ]; then
    systemctl condrestart %{serv_name}.service
else
    if [ -s /etc/init.d/%{serv_name} ]; then
        service %{serv_name} condrestart
    fi
fi


%package nipc
Summary:	GSM Network In a PC based on YateBTS
Group:		Applications/Communication
Requires:	%{name} = %{version}-%{release}
Requires:	yate-scripts = 6.4.1
Requires:	apache-mod_php
%if %{nosdr}
Requires(post):	gawk
Suggests:	pysim
%endif
Obsoletes:	yate-bts-nib
Conflicts:	yate-bts-nib

%description nipc
Scripts and support executables that implement a GSM Network In a PC.

%files nipc
%defattr(-, root, root)
%{scrdir}/nipc_auth.sh
%{scrdir}/do_*
%{scrdir}/nipc.js
%{scrdir}/welcome.js
%{scrdir}/custom_sms.js
%{shrdir}/sounds/*
/var/www/html/nipc
%if %{nosdr}
%dir %{shrdir}/nipc_web
%{shrdir}/nipc_web/*
%config(noreplace) %{shrdir}/nipc_web/.htaccess
%config(noreplace) %{shrdir}/nipc_web/config.php
%else
%{cfgdir}/bts-extmod.conf
%endif
%config(noreplace) %{cfgdir}/subscribers.conf

%post nipc
%if %{nosdr}
sed -i 's/^ *\(roaming\|nipc\) *=.*$/;; \0/' %{cfgdir}/javascript.conf
if ! grep -q '; Installed by yate-bts-nipc' %{cfgdir}/javascript.conf 2>/dev/null; then
    if grep -q '^ *\[general\]' %{cfgdir}/javascript.conf 2>/dev/null; then
	awk '/^ *\[/{sect=0}
	/^ *\[general\]/{sect=1}
	/^ *routing *=/{if(sect==2)sect=3}
	{if(sect==3){print ";; " $0;sect=2} else print;
	 if(sect==1){print "; Installed by yate-bts-nipc, do not remove this comment line\nrouting=welcome.js\n";sect=2}
	}' <%{cfgdir}/javascript.conf >%{cfgdir}/javascript.conf.tmp
	mv -f %{cfgdir}/javascript.conf.tmp %{cfgdir}/javascript.conf
    else
	cat <<-EOF >>%{cfgdir}/javascript.conf
	[general]
	; Installed by yate-bts-nipc, do not remove this comment line
	routing=welcome.js

	EOF
    fi
fi
if ! grep -q '^ *mode *=' %{cfgdir}/ybts.conf 2>/dev/null; then
    if grep -q '^ *\[ybts\]' %{cfgdir}/ybts.conf 2>/dev/null; then
	awk '/^ *\[/{sect=0}
	/^ *\[ybts\]/{sect=1}
	/^ *mode *=/{if(sect==2)sect=3}
	{if(sect==3){print ";; " $0;sect=2} else print;
	 if(sect==1){print "; Installed by yate-bts-nipc, do not remove this comment line\nmode=nipc\n";sect=2}
	}' <%{cfgdir}/ybts.conf >%{cfgdir}/ybts.conf.tmp
	mv -f %{cfgdir}/ybts.conf.tmp %{cfgdir}/ybts.conf
    fi
fi
if ! grep -q '; Installed by yate-bts-nipc' %{cfgdir}/extmodule.conf 2>/dev/null; then
    if grep -q '^ *\[scripts\]' %{cfgdir}/extmodule.conf 2>/dev/null; then
	awk '/^ *\[/{sect=0}
	/^ *\[scripts\]/{sect=1}
	/^ *gsm_auth\.sh/{if(sect==2)sect=3}
	/^ *nipc_auth\.sh/{if(sect==2)sect=3}
	{if(sect==3){print ";; " $0;sect=2} else print;
	 if(sect==1){print "; Installed by yate-bts-nipc, do not remove this comment line\nnipc_auth.sh\n";sect=2}
	}' <%{cfgdir}/extmodule.conf >%{cfgdir}/extmodule.conf.tmp
	mv -f %{cfgdir}/extmodule.conf.tmp %{cfgdir}/extmodule.conf
    else
	cat <<-EOF >>%{cfgdir}/extmodule.conf
	[scripts]
	; Installed by yate-bts-nipc, do not remove this comment line
	nipc_auth.sh

	EOF
    fi
fi
chgrp -R apache %{cfgdir}
chmod -R g+rw %{cfgdir}
%else
test "X$1" = "X1" && %{_datadir}/yate/scripts/rpm_restore.sh %{name}-nipc
%endif


%package roaming
Summary:	SIP based GSM roaming support for YateBTS
Group:		Applications/Communication
Requires:	%{name} = %{version}-%{release}
Requires:	yate-scripts = 6.4.1
%if %{nosdr}
Requires(post):	gawk
%endif

%description roaming
Scripts that implement SIP registration from YateBTS to a remote YateUCN server.

%files roaming
%defattr(-, root, root)
%{scrdir}/roaming.js
%{scrdir}/handover.js
%if %{nosdr}
%{scrdir}/lib_str_util.js
%endif

%post roaming
%if %{nosdr}
sed -i 's/^ *\(roaming\|nipc\) *=.*$/;; \0/' %{cfgdir}/javascript.conf
if ! grep -q '^ *mode *=' %{cfgdir}/ybts.conf 2>/dev/null; then
    if grep -q '^ *\[ybts\]' %{cfgdir}/ybts.conf 2>/dev/null; then
	awk '/^ *\[/{sect=0}
	/^ *\[ybts\]/{sect=1}
	/^ *mode *=/{if(sect==2)sect=3}
	{if(sect==3){print ";; " $0;sect=2} else print;
	 if(sect==1){print "; Installed by yate-bts-roaming, do not remove this comment line\nmode=roaming\n";sect=2}
	}' <%{cfgdir}/ybts.conf >%{cfgdir}/ybts.conf.tmp
	mv -f %{cfgdir}/ybts.conf.tmp %{cfgdir}/ybts.conf
    fi
fi
%endif
if ! grep -q '; Installed by yate-bts-roaming +handover\|updated=\|locked=' %{cfgdir}/ysipchan.conf 2>/dev/null; then
    mv -f -n %{cfgdir}/ysipchan.conf %{cfgdir}/ysipchan.conf.rpmold
    cat <<-EOF >%{cfgdir}/ysipchan.conf
	; Installed by yate-bts-roaming +handover, do not remove this comment line

	[general]
	updated=`date -u '+%%A, %%d-%%b-%%y %%H:%%M:%%S GMT'` from package installer
	locked=false
	lazy100=yes
	transfer=no
	privacy=yes
	generate=yes
	rtp_start=yes
	auth_foreign=yes
	autochangeparty=yes
	update_target=yes
	body_encoding=hex
	async_generic=yes
	sip_req_trans_count=5
	useragent=YateBTS/6.1.1

	[codecs]
	default=disable
	gsm=enable

	[message]
	enable=yes
	auth_required=false

	[options]
	enable=no

	[methods]
	options=no
	info=no

	EOF
fi


%prep
%setup -q -n %{name}

# older rpmbuild uses these macro basic regexps
%define _requires_exceptions pear
# newer rpmbuild needs these global extended regexps
%global __requires_exclude pear

%define local_find_requires %{_builddir}/%{name}/local-find-requires
#
%{__cat} <<EOF >%{local_find_requires}
#! /bin/sh
%{__find_requires} | grep -v '^\(perl\|pear\)' | grep -v '.php'
exit 0
EOF
#
chmod +x %{local_find_requires}
%define __find_requires %{local_find_requires}

%if "%{no_auto_deps}" == "1"
%define local_find_provides %{_builddir}/%{name}/local-find-provides
#
%{__cat} <<EOF >%{local_find_provides}
#! /bin/sh
%{__find_provides} | grep -v '\.yate$'
exit 0
EOF
#
chmod +x %{local_find_provides}
%define _use_internal_dependency_generator 0
%define __find_provides %{local_find_provides}
%define __perl_requires /bin/true
%endif

%build
./configure --prefix=%{prefix} --sysconfdir=/etc --mandir=%{prefix}/share/man \
	--with-conf=%{cfgdir} %{?extra_conf}
make %{stripped} %{?extra_make}
%{?extra_step}

%install
make install DESTDIR=%{buildroot} %{?extra_make}
mkdir -p %{buildroot}/var/www/html
%if %{nosdr}
ln -sf %{shrdir}/nipc_web %{buildroot}/var/www/html/nipc
%else
cp -rp nipc/redir %{buildroot}/var/www/html/nipc
cp -p scripts/*.js* %{buildroot}%{scrdir}/
echo -e '[scripts]\nbts_config=bts_config.js' > %{buildroot}%{cfgdir}/bts-jscript.conf
echo -e '[scripts]\nnipc_auth.sh' > %{buildroot}%{cfgdir}/bts-extmod.conf
mkdir -p %{buildroot}%{shrdir}/api
echo '<?php global $bts_version; $bts_version = "%{version}-%{release}"; ?>' > %{buildroot}%{shrdir}/api/bts_version.php
rm %{buildroot}%{cfgdir}/ybts.conf
rm %{buildroot}%{scrdir}/lib_str_util.js
rm -rf %{buildroot}%{shrdir}/nipc_web
%endif
%if "%{?extra_inst}"
export DESTDIR=%{buildroot}
%{?extra_inst}
%endif

%clean
rm -rf %{buildroot}

%changelog
* Wed Mar 29 2017 Paul Chitescu <paulc@null.ro>
- Added support for extra build steps

* Mon Aug 24 2015 Paul Chitescu <paulc@null.ro>
- Removed hardware support subpackages

* Thu Apr 24 2014 Paul Chitescu <paulc@null.ro>
- Added bladerf subpackage

* Mon Mar 17 2014 Paul Chitescu <paulc@null.ro>
- Added NiPC Web interface files

* Mon Dec 09 2013 Paul Chitescu <paulc@null.ro>
- Created specfile
