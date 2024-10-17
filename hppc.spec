%{?_javapackages_macros:%_javapackages_macros}

Name:          hppc
Version:       0.7.1
Release:       5.1
Summary:       High Performance Primitive Collections for Java
License:       ASL 2.0
Group:         Development/Java
URL:           https://labs.carrotsearch.com/hppc.html
Source0:       https://github.com/carrotsearch/hppc/archive/%{version}.tar.gz

BuildRequires: maven-local
BuildRequires: mvn(com.google.guava:guava)
BuildRequires: mvn(commons-io:commons-io)
BuildRequires: mvn(org.apache.ant:ant)
BuildRequires: mvn(org.apache.ant:ant-junit)
BuildRequires: mvn(org.apache.maven:maven-core)
BuildRequires: mvn(org.apache.maven:maven-plugin-api)
BuildRequires: mvn(org.apache.maven.plugin-tools:maven-plugin-annotations)
BuildRequires: mvn(org.apache.maven.plugins:maven-plugin-plugin)
BuildRequires: mvn(org.apache.velocity:velocity)
BuildRequires: mvn(org.sonatype.oss:oss-parent:pom:)
BuildRequires: mvn(org.antlr:antlr4)
BuildRequires: mvn(org.antlr:antlr4-maven-plugin)

%if 0
# hppc-benchmarks deps
BuildRequires: mvn(it.unimi.dsi:fastutil)
BuildRequires: mvn(net.openhft:koloboke-impl-jdk6-7:0.6.6)
BuildRequires: mvn(org.openjdk.jmh:jmh-core)
BuildRequires: mvn(org.openjdk.jmh:jmh-generator-annprocess)

# test deps
BuildRequires: mvn(junit:junit)
BuildRequires: mvn(com.carrotsearch.randomizedtesting:junit4-maven-plugin)
BuildRequires: mvn(com.carrotsearch.randomizedtesting:randomizedtesting-runner)
BuildRequires: mvn(org.assertj:assertj-core)
%endif

BuildArch:     noarch

%description
Fundamental data structures (maps, sets, lists, stacks, queues) generated for
combinations of object and primitive types to conserve JVM memory and speed
up execution.

%package templateprocessor
Summary:       HPPC Template Processor

%description templateprocessor
Template Processor and Code Generation for HPPC.

%package javadoc
Summary:       Javadoc for HPPC

%description javadoc
This package contains javadoc for HPPC.

%prep
%setup -q
find . -name "*.class" -print -delete
find . -name "*.jar" -print -delete

# Unavailable deps
%pom_disable_module %{name}-benchmarks
%pom_remove_plugin :junit4-maven-plugin
%pom_remove_plugin :forbiddenapis
%pom_remove_plugin :junit4-maven-plugin hppc
# Unneeded task
%pom_remove_plugin -r :maven-assembly-plugin

# Convert from dos to unix line ending
for file in CHANGES.txt; do
 sed -i.orig 's|\r||g' $file
 touch -r $file.orig $file
 rm $file.orig
done

%mvn_file :%{name} %{name}
%mvn_package :%{name}::esoteric:
%mvn_file :%{name}-template-processor %{name}-templateprocessor
%mvn_package :%{name}-template-processor %{name}-templateprocessor

%build

# Disable test for now. Unavailable test deps
%mvn_build -f

%install
%mvn_install

%files -f .mfiles
%doc CHANGES.txt README.txt
%doc LICENSE.txt NOTICE.txt

%files templateprocessor -f .mfiles-%{name}-templateprocessor
%doc LICENSE.txt NOTICE.txt

%files javadoc -f .mfiles-javadoc
%doc LICENSE.txt NOTICE.txt

%changelog
* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Sat Jan 23 2016 gil cattaneo <puntogil@libero.it> 0.7.1-2
- install "esoteric" artifact

* Wed Jan 20 2016 Alexander Kurtakov <akurtako@redhat.com> 0.7.1-1
- Update to upstream 0.7.1 release.

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Thu Feb 05 2015 gil cattaneo <puntogil@libero.it> 0.6.1-2
- introduce license macro

* Wed Dec 17 2014 gil cattaneo <puntogil@libero.it> 0.6.1-1
- update to 0.6.1

* Tue Jun 17 2014 gil cattaneo <puntogil@libero.it> 0.5.3-4
- fix BR list

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.5.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sun Dec 29 2013 gil cattaneo <puntogil@libero.it> 0.5.3-2
- add templateprocessor sub-package

* Thu Dec 05 2013 gil cattaneo <puntogil@libero.it> 0.5.3-1
- 0.5.3

* Sun Aug 25 2013 gil cattaneo <puntogil@libero.it> 0.5.2-1
- initial rpm

