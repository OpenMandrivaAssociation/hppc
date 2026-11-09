Name:		hppc
Version:	0.13.0
Release:	1
Summary:	High performance primitive collections for Java
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/carrotsearch/hppc
Source0:	https://github.com/carrotsearch/hppc/archive/refs/tags/%{version}.tar.gz#/hppc-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildRequires:	antlr4-tool = 4.13.2
BuildRequires:	antlr4 = 4.13.2
BuildRequires:	velocity-engine-core >= 2.4.1
BuildRequires:	apache-commons-lang3 >= 3.21.0
BuildRequires:	slf4j
BuildRequires:	mvn(org.antlr:antlr4-runtime)
BuildRequires:	mvn(org.apache.velocity:velocity-engine-core)
BuildRequires:	mvn(org.apache.commons:commons-lang3)
BuildRequires:	mvn(org.slf4j:slf4j-api)
BuildSystem:	maven
BuildOption(install):	--file-name hppc --link %{name}

Obsoletes:	hppc-templateprocessor < %{EVRD}
Obsoletes:	hppc-javadoc < %{EVRD}

# Jars the explicit BuildRequires install. build-classpath is not used.
%global gen_cp %{_javadir}/antlr4-runtime.jar:%{_javadir}/velocity-engine-core.jar:%{_javadir}/commons-lang3.jar:%{_javadir}/slf4j/slf4j-api.jar:%{_javadir}/slf4j/slf4j-nop.jar

%description
HPPC is primitive maps, sets, lists, stacks and queues. 0.13.0 requires
Java 21. It fixes BitSet updates, KTypeArrayList and KTypeArrayDeque
resizing, hash-container removeAll, and KTypePgmIndex rank and range
queries. The template processor stays a build tool and is not installed.
The generic Intrinsics class is expanded away and is not in the jar.

%prep
%autosetup -n hppc-%{version}
# The tag ships a Gradle wrapper jar. Nothing here runs Gradle.
rm -rf gradle gradlew gradlew.bat hppc-benchmarks hppc-examples .github .claude
find . -name '*.gradle' -delete
find . -name '*.gradle.kts' -delete
find . -name '*.toml' -delete
if find . \( -name '*.jar' -o -name '*.class' \) | grep -q . ; then
	echo "prebuilt Java binary in the sources"
	find . \( -name '*.jar' -o -name '*.class' \)
	exit 1
fi

# carrotsearch-console pulls SLF4J 2 and log4j. The processor only uses
# it to parse three arguments, so the build calls execute() directly.
python - <<'PY'
from pathlib import Path
p = Path("hppc-template-processor/src/main/java/com/carrotsearch/hppc/generator/TemplateProcessor.java")
text = p.read_text(encoding="utf-8")
old_imports = """import com.carrotsearch.console.jcommander.Parameter;
import com.carrotsearch.console.launcher.Command;
import com.carrotsearch.console.launcher.ExitCode;
import com.carrotsearch.console.launcher.ExitCodes;
import com.carrotsearch.console.launcher.Launcher;
import com.carrotsearch.console.launcher.Loggers;
"""
new_imports = "import org.slf4j.LoggerFactory;\n"
if old_imports not in text:
    raise SystemExit("console imports missing")
text = text.replace(old_imports, new_imports, 1)
old_cls = "public class TemplateProcessor extends Command<ExitCode> {"
if old_cls not in text:
    raise SystemExit("class declaration missing")
text = text.replace(old_cls, "public class TemplateProcessor {", 1)
old_fields = """  @Parameter(names = {"--incremental"})
  public boolean incremental;

  @Parameter(
      names = {"--templates"},
      required = true)
  public Path templatesDir;

  @Parameter(
      names = {"--output"},
      required = true)
  public Path outputDir;
"""
new_fields = """  public boolean incremental;
  public Path templatesDir;
  public Path outputDir;
"""
if old_fields not in text:
    raise SystemExit("parameter fields missing")
text = text.replace(old_fields, new_fields, 1)
old_main = """  public static void main(String[] args) {
    ExitCode exitCode = new Launcher().runCommand(new TemplateProcessor(), args);
    System.exit(exitCode.processReturnValue());
  }

  @Override
  protected ExitCode run() {
    try {
      logger = Loggers.CONSOLE;
      return execute();
    } catch (IOException e) {
      logger.error("I/O exception occurred.", e);
      return ExitCodes.ERROR_INTERNAL;
    }
  }

  private ExitCode execute() throws IOException {
"""
new_main = """  public static void main(String[] args) {
    TemplateProcessor processor = new TemplateProcessor();
    for (int i = 0; i < args.length; i++) {
      String arg = args[i];
      if (arg.equals("--incremental")) {
        processor.incremental = true;
      } else if (arg.equals("--templates")) {
        processor.templatesDir = Path.of(args[++i]);
      } else if (arg.equals("--output")) {
        processor.outputDir = Path.of(args[++i]);
      } else {
        throw new IllegalArgumentException(arg);
      }
    }
    if (processor.templatesDir == null || processor.outputDir == null) {
      throw new IllegalArgumentException("missing --templates or --output");
    }
    processor.logger = LoggerFactory.getLogger(TemplateProcessor.class);
    try {
      processor.execute();
    } catch (IOException e) {
      processor.logger.error("I/O exception occurred.", e);
      System.exit(1);
    }
  }

  private void execute() throws IOException {
"""
if old_main not in text:
    raise SystemExit("main missing")
text = text.replace(old_main, new_main, 1)
old_return = "    return ExitCodes.SUCCESS;\n"
if old_return not in text:
    raise SystemExit("success return missing")
text = text.replace(old_return, "    return;\n", 1)
if "ExitCode" in text or "carrotsearch.console" in text:
    raise SystemExit("console types remain")
p.write_text(text, encoding="utf-8")
PY

mkdir -p generated-parser proc-classes generated-templates
# Absolute grammar paths. A relative grammar path is appended to -o, and the
# parser then cannot see the lexer tokens.
outdir="$(pwd)/generated-parser/com/carrotsearch/hppc/generator/parser"
gramdir="$(pwd)/hppc-template-processor/src/main/antlr/com/carrotsearch/hppc/generator/parser"
antlr4 -visitor -package com.carrotsearch.hppc.generator.parser \
	-o "$outdir" \
	"$gramdir/JavaLexer.g4" \
	"$gramdir/JavaParser.g4"
test -f "$outdir/JavaParser.java"
test -f "$outdir/JavaParserBaseVisitor.java"
find hppc-template-processor/src/main/java generated-parser -name '*.java' > proc-sources.list
javac --release 21 -encoding UTF-8 -cp "%{gen_cp}" -d proc-classes @proc-sources.list
java -cp "proc-classes:%{gen_cp}" com.carrotsearch.hppc.generator.TemplateProcessor \
	--templates hppc/src/main/templates \
	--output generated-templates

python - <<'PY'
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

generated = list(Path("generated-templates").rglob("*.java"))
if len(generated) != 525:
    raise SystemExit("generated java count " + str(len(generated)))
parsers = list(Path("generated-parser").rglob("*.java"))
if len(parsers) != 6:
    raise SystemExit("parser java count " + str(len(parsers)))
dest = Path("hppc/src/main/java")
for src in generated:
    rel = src.relative_to("generated-templates")
    target = dest / rel
    if target.exists():
        raise SystemExit("generated file collides with " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)
sources = list(dest.rglob("*.java"))
if len(sources) != 547:
    raise SystemExit("combined java count " + str(len(sources)))
module_info = dest / "module-info.java"
if not module_info.is_file():
    raise SystemExit("module-info missing")
# Current OpenJDK provides jmod(java.base) only. The descriptor also
# requires java.logging and static jdk.management, which would pull the
# java-13 package. An automatic module reads the JDK without that.
module_info.unlink()
if len(list(dest.rglob("*.java"))) != 546:
    raise SystemExit("java count after dropping module-info")
if list(dest.rglob("Intrinsics.java")):
    raise SystemExit("Intrinsics leaked into the library sources")
if not (dest / "com/carrotsearch/hppc/IntIntHashMap.java").is_file():
    raise SystemExit("IntIntHashMap was not generated")
if not (dest / "com/carrotsearch/hppc/ByteArrayList.java").is_file():
    raise SystemExit("ByteArrayList was not generated")

NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def tag(name):
    return "{" + NS + "}" + name

def add(parent, name, text):
    node = ET.SubElement(parent, tag(name))
    node.text = text
    return node

root = ET.Element(tag("project"))
add(root, "modelVersion", "4.0.0")
add(root, "groupId", "com.carrotsearch")
add(root, "artifactId", "hppc")
add(root, "version", "%{version}")
add(root, "name", "High Performance Primitive Collections")
props = ET.SubElement(root, tag("properties"))
add(props, "maven.compiler.release", "21")
add(props, "project.build.sourceEncoding", "UTF-8")
build = ET.SubElement(root, tag("build"))
add(build, "sourceDirectory", "hppc/src/main/java")
ET.ElementTree(root).write("pom.xml", encoding="utf-8", xml_declaration=True)
pom = Path("pom.xml").read_text(encoding="utf-8")
if "<maven.compiler.release>21</maven.compiler.release>" not in pom:
    raise SystemExit("compiler release missing")
if "<sourceDirectory>hppc/src/main/java</sourceDirectory>" not in pom:
    raise SystemExit("source directory missing")
PY

%build -a
python - <<'PY'
import zipfile
from pathlib import Path
jar = Path("target/hppc-%{version}.jar")
if not jar.is_file():
    raise SystemExit("jar missing")
with zipfile.ZipFile(jar) as z:
    names = set(z.namelist())
    data = z.read("com/carrotsearch/hppc/IntIntHashMap.class")
major = data[6] * 256 + data[7]
if major != 65:
    raise SystemExit("class major " + str(major))
for banned in (
    "module-info.class",
    "com/carrotsearch/hppc/Intrinsics.class",
    "com/carrotsearch/hppc/generator/TemplateProcessor.class",
):
    if banned in names:
        raise SystemExit("unexpected " + banned)
if "com/carrotsearch/hppc/ByteArrayList.class" not in names:
    raise SystemExit("ByteArrayList missing from the jar")
PY
cat > manifest-addition <<'EOF'
Automatic-Module-Name: com.carrotsearch.hppc
EOF
jar ufm target/hppc-%{version}.jar manifest-addition
java --module-path target/hppc-%{version}.jar --describe-module com.carrotsearch.hppc > module.txt
grep -q '^com.carrotsearch.hppc' module.txt
if grep -q 'java.logging' module.txt; then
	echo "module requires java.logging"
	exit 1
fi
if grep -q 'jdk.management' module.txt; then
	echo "module requires jdk.management"
	exit 1
fi

%files -f .mfiles
%doc LICENSE.txt NOTICE.txt CHANGES.txt README.md
