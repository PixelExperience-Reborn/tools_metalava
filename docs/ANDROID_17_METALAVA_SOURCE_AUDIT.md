# PixelExperience-Reborn Android 17 — tools/metalava source audit (P2, matrix row 162)

## Decision — 2026-11-06

**Keep the exact official AOSP17 Metalava source in the active manifest. Do not replace it with the old `PixelExperience-Reborn/tools_metalava` fork.** This is a deliberate positive compatibility decision for framework SDK/API generation, not omission of PE functionality.

Metalava is a **host API metadata tool** used for Android API signature files, compatibility/lint analysis, SDK stubs and `android.jar` generation. It is **not** a Qualcomm/mondrian hardware feature. Prematurely overriding it could invalidate Android17 Soong dependencies and API compatibility checks long before a new PE-Reborn device tree is built.

## Historical PixelExperience identity and actual delta

- Old `seventeen` and `fourteen` branch SHA: `016bbd20780ea4b762c8cfa08009a177dff3d3ce`, a **2024-01-30 merge of Android `android-14.0.0_r21`**, not Android17 source.
- First merge parent `4c4b3048c8e69932dd226989234cba38d8a49e36`.
- Second merge parent `4b6ef752b81bd3a3441c54bd08475b8e2970ba22`.
- **All three trees have the identical SHA `6856c264cacf99c77e8bc54ed98cf7cd63f90881`**. GitHub comparisons also show **zero file changes** versus both merge parents. Therefore the import contains **no unique PE source delta to port**.
- The Android14-style root `Android.bp` owns a monolithic `java_binary_host { name: "metalava" }` drawing from top-level `src/main/java` and `stub-annotations`. It uses the old `--copy-annotations` invocation and Kotlin language level 1.6/JVM8 in the historical Gradle config. These rules must **not** be mechanically adapted to Android17.

## Official immutable AOSP17 source and module graph

The reviewed source is **`platform/tools/metalava`** under official annotated tag **`android-17.0.0_r1`**:

- Tag object `060c511f4caf2f9ac8a3de83d87422c60efa5dd1`.
- Peeled Git commit **`e33bb96bcd3279859f4d824ba3d17a36b56c2f68`**.
- Exact root tree **`5885d581be37f303690dadb64e605fc0c3cf7334`**.
- Modern layout separates `metalava/Android.bp` (the `metalava` host executable), `metalava-model/`, `metalava-model-psi/`, `metalava-model-source/`, `metalava-model-text/`, `metalava-model-turbine/`, `metalava-reporter/`, `metalava-testing/`, `stub-annotations/`, the Gradle integration suites, and `version.properties`.
- The root `Android.bp` provides `metalava-signature-reader`, `metalava-version`, `stub-annotations` and the modern `private-stub-annotations` generator. It uses `make-annotations-package-private`, not the archived `--copy-annotations` command. The host tool module `metalava` has been moved into `metalava/Android.bp` with modular source dependencies. Do not move it back.
- Keep official Soong ownership of `metalava` and its libraries and dependency paths; any Android17 framework or SDK changes must be tested against this upstream API toolchain.

Official references: https://android.googlesource.com/platform/tools/metalava/+/refs/tags/android-17.0.0_r1 and https://android.googlesource.com/platform/tools/metalava/+/refs/tags/android-17.0.0_r1/Android.bp and https://android.googlesource.com/platform/tools/metalava/+/refs/tags/android-17.0.0_r1/metalava/Android.bp .

## PixelExperience-Reborn AOSP17 manifest decision

- `PixelExperience-Reborn/manifest` branch `port/a17-aosp17-manifest-20261102` has baseline project `path="tools/metalava"`, `name="platform/tools/metalava"`, `groups="pdk,tools"`, remote `aosp`, revision `refs/tags/android-17.0.0_r1`.
- The latest reviewed `default.xml` includes only `aosp17_pe_p2_kernel_configs.xml`, indirectly retaining the AOSP source as the **only** `tools/metalava` owner in all 25 staged profiles.
- The `tools/validate_aosp17_base_profiles.py` validator now protects this official source path and rejects the legacy repository name `tools_metalava`. A negative regression test attempts to replace the official project with the Android14 PE fork and confirms rejection.
- **No PE override, source pin, extra manifest profile, API signature change or new product/device tree is introduced.** The old `seventeen` branch is preserved. The project is already available from official AOSP17.

## Source-only CI checks

The review CI checks the exact old PE SHA/merge ancestry, **both parent trees**, zero effective file difference, and legacy module position. It fetches the exact official Android17 tag and verifies its peeled commit/tree, modern `Android.bp` modules, dependencies and stub-annotation command. It verifies baseline manifest groups/remote, all 25 staged XML profiles, 13 manifest regression tests and the effective `repo manifest` graph of 1069 default-selected projects.

CI is **source-only**: it is *not* evidence that the full Soong project builds. The old Android14 fork is not compiled and no unreviewed Gradle dependencies are downloaded.

## Required integration testing once a build server and independent PE device graph exist

1. Complete a clean `repo sync` of the reviewed Android17 manifest, without importing old Android14 PE snippets.
2. Validate Soong bootstrap and Metalava host module including its Kotlin, PSI/UAST, version resource and model dependencies on the actual Android17 source graph.
3. Run the official Android17 `metalava` module tests, SDK stub/API signature generation, `checkapi`/API-lint compatibility checks and API surface changes coming from the independently ported PE frameworks/base.
4. Verify module and API compatibility for Settings, SystemUI, framework changes, sdk/hiddenapi and prebuilts/sdk. Avoid introducing legacy `--copy-annotations` or misplaced `metalava` modules.
5. Only later, after separate PE-Reborn mondrian-only device/common/vendor/kernel sources are completed, run full device build, CTS/VTS, SELinux/VINTF and physical POCO F5 Pro / Redmi K60 boot.

**Status: legacy-delta + official AOSP17 Metalava source/manifest audit. Real compilation and device testing remain OPEN.**

## Review links

- Old PE fork: https://github.com/PixelExperience-Reborn/tools_metalava/tree/seventeen
- Historical Android14 merge: https://github.com/PixelExperience-Reborn/tools_metalava/commit/016bbd20780ea4b762c8cfa08009a177dff3d3ce
- Official AOSP17 source: https://android.googlesource.com/platform/tools/metalava/+/refs/tags/android-17.0.0_r1
- Reviewed Android17 manifest: https://github.com/PixelExperience-Reborn/manifest/tree/port/a17-aosp17-manifest-20261102
