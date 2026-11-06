#!/usr/bin/env python3
"""Source-only Android17 Metalava audit, intentionally no SDK/ROM build.

Never substitute the Android14 PE fork for the official 2026 API toolchain.
Requires: checked-out PE audit branch with old merge parents, shallow official
android-17.0.0_r1 Git fetch, reviewed Android17 manifest checkout.
"""
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

OLD_MERGE = "016bbd20780ea4b762c8cfa08009a177dff3d3ce"
OLD_PARENTS = [
    "4c4b3048c8e69932dd226989234cba38d8a49e36",
    "4b6ef752b81bd3a3441c54bd08475b8e2970ba22",
]
OLD_TREE = "6856c264cacf99c77e8bc54ed98cf7cd63f90881"
AOSP17_COMMIT = "e33bb96bcd3279859f4d824ba3d17a36b56c2f68"
AOSP17_TREE = "5885d581be37f303690dadb64e605fc0c3cf7334"
AOSP17_TAG = "android-17.0.0_r1"
AOSP17_MODULES = [
    "metalava-model",
    "metalava-model-psi",
    "metalava-model-source",
    "metalava-model-text",
    "metalava-model-turbine",
    "metalava-reporter",
]
REQUIRED_ROOTS = {
    "Android.bp",
    "metalava",
    "metalava-model",
    "metalava-model-psi",
    "metalava-model-source",
    "metalava-model-text",
    "metalava-model-turbine",
    "metalava-reporter",
    "metalava-testing",
    "stub-annotations",
    "version.properties",
}

def require(ok: bool, message: str):
    if not ok:
        raise RuntimeError(message)

def git(repo: Path, *args: str):
    return subprocess.check_output(["git", "-C", str(repo), *args],
                                   text=True).strip()

def module_decl(text: str, module_type: str, name: str) -> bool:
    return re.search(
        rf'\b{re.escape(module_type)}\s*\{{\s*name:\s*"{re.escape(name)}"',
        text,
    ) is not None

def check_legacy(root: Path):
    ref = git(root, "rev-parse", "refs/remotes/origin/seventeen")
    require(ref == OLD_MERGE, f"legacy PE head moved; re-audit: {ref}")
    parents = git(root, "rev-list", "--parents", "-n", "1", OLD_MERGE).split()
    require(parents == [OLD_MERGE, *OLD_PARENTS],
            f"unexpected Android14 merge parents: {parents}")
    for ref in [OLD_MERGE, *OLD_PARENTS]:
        tree = git(root, "rev-parse", f"{ref}^{{tree}}")
        require(tree == OLD_TREE,
                f"legacy source tree differs from both AOSP14 parents: {ref}, {tree}")
    require(git(root, "diff", "--name-only", OLD_PARENTS[0], OLD_MERGE) == "",
            "legacy PE has files differing from its first AOSP14 parent")
    require(git(root, "diff", "--name-only", OLD_PARENTS[1], OLD_MERGE) == "",
            "legacy PE has files differing from its second AOSP14 parent")
    bp = git(root, "show", f"{OLD_MERGE}:Android.bp")
    require(module_decl(bp, "java_binary_host", "metalava"),
            "old Metalava tool layout changed")
    require("--copy-annotations" in bp and
            "src/main/java/**/*.kt" in bp,
            "old Android14 Metalava command/source structure unexpectedly changed")
    roots = set(git(root, "ls-tree", "--name-only", OLD_MERGE).splitlines())
    require("src" in roots and "metalava-model" not in roots,
            "old Metalava tree no longer has historical layout")
    print("PASS: archived PE branch points to Android14 source, not Android17")
    print("PASS: old PE merge and both AOSP14 parent trees identical; no PE file delta")
    print("PASS: legacy Metalava's monolithic root Soong module detected")

def check_aosp17(root: Path):
    commit = git(root, "rev-parse", "FETCH_HEAD^{commit}")
    tree = git(root, "rev-parse", "FETCH_HEAD^{tree}")
    require(commit == AOSP17_COMMIT and tree == AOSP17_TREE,
            f"unexpected AOSP17 {AOSP17_TAG} commit/tree: {commit}/{tree}")
    roots = set(git(root, "ls-tree", "--name-only", "FETCH_HEAD").splitlines())
    require(REQUIRED_ROOTS.issubset(roots),
            f"missing modern AOSP17 source modules: {REQUIRED_ROOTS - roots}")
    require("src" not in roots,
            "old monolithic Metalava source root unexpectedly revived")
    main_bp = git(root, "show", "FETCH_HEAD:metalava/Android.bp")
    root_bp = git(root, "show", "FETCH_HEAD:Android.bp")
    model_bp = git(root, "show", "FETCH_HEAD:metalava-model/Android.bp")
    require(module_decl(main_bp, "java_binary_host", "metalava"),
            "Android17 metalava host tool module moved or renamed")
    require(not module_decl(root_bp, "java_binary_host", "metalava"),
            "Android17 metalava host binary unexpectedly declared in old root")
    for module in AOSP17_MODULES:
        require(f'"{module}"' in main_bp,
                f"Android17 metalava missing its {module} dependency")
    require(module_decl(root_bp, "java_library_host",
                        "metalava-signature-reader"),
            "modern Android17 Metalava signature reader missing")
    require(module_decl(root_bp, "filegroup", "metalava-version"),
            "modern Metalava version resource owner missing")
    require(module_decl(model_bp, "java_library_host", "metalava-model"),
            "modern model source graph missing")
    require("make-annotations-package-private" in root_bp,
            "modern Android17 stub annotation generation changed")
    require("--copy-annotations" not in root_bp,
            "old Android14 stub annotation command reintroduced")
    print("PASS: exact official AOSP17 r1 Metalava commit/tree and modular source roots")
    print("PASS: modern Soong host binary, model dependencies and SDK annotations")

def check_manifest(root: Path):
    baseline = ET.parse(root / "aosp17_reference.xml").getroot()
    default = baseline.find("default")
    require(default is not None
            and default.get("remote") == "aosp"
            and default.get("revision") == "refs/tags/android-17.0.0_r1",
            "wrong official AOSP17 manifest tag/remote")
    projects = [p for p in baseline.findall("project")
                if (p.get("path") or p.get("name")) == "tools/metalava"]
    require(len(projects) == 1
            and projects[0].get("name") == "platform/tools/metalava",
            "AOSP17 baseline Metalava source owner replaced")
    require(projects[0].get("groups") == "pdk,tools",
            "AOSP17 metalava groups modified")
    require(not any(p.get("name") == "tools_metalava"
                    for p in baseline.findall("project")),
            "legacy PE fork unexpectedly imported")
    active = ET.parse(root / "default.xml").getroot()
    require(len(active) == 1
            and active[0].tag == "include"
            and active[0].get("name") == "aosp17_pe_p2_kernel_configs.xml",
            "latest staged manifest changed: re-review source selection")
    subprocess.run([sys.executable,
                    str(root / "tools/validate_aosp17_base_profiles.py")],
                   cwd=root, check=True)
    print("PASS: official AOSP17 Metalava retained in all reviewed profiles")

def main():
    require(len(sys.argv) == 4,
            "usage: check_metalava_source.py OLD_PE_ROOT AOSP17_GIT_ROOT AOSP17_MANIFEST_ROOT")
    old, aosp17, manifest = [Path(x).resolve() for x in sys.argv[1:]]
    require(all(p.is_dir() for p in (old, aosp17, manifest)),
            "one or more source checkouts are missing")
    check_legacy(old)
    check_aosp17(aosp17)
    check_manifest(manifest)
    print("PASS: row 162 AOSP17 Metalava source-only audit")
    print("NOT TESTED: repo sync, Soong build, Kotlin/Gradle runtime, metalava --api,"
          " checkapi, SDK stubs, CTS/VTS, mondrian boot")

if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError,
            ET.ParseError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
