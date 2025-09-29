from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, collect_libs
import os


class AsconConan(ConanFile):
    name = "ascon"
    # Adjust version as appropriate (could be synchronized with upstream tag)
    version = "1.0.0"
    license = "CC0-1.0"
    url = "https://github.com/ascon/ascon-c"
    description = "Reference, optimized and masked C/ASM implementations of Ascon (NIST SP 800-232)"
    topics = ("cryptography", "ascon", "aead", "hash", "mac", "prf")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"
    exports_sources = "ascon-c/*", "LICENSE"
    no_copy_source = True

    # Comma separated lists to stay user friendly for CLI overrides.
    options = {
        "with_tests": [True, False],
        "alg_list": "ANY",  # free-form string list or "ANY" for defaults
        "impl_list": "ANY", # free-form string list or "ANY"
        "version_list": "ANY",  # free-form string list or "ANY"
    }
    default_options = {
        "with_tests": False,
        "alg_list": "ANY",
        "impl_list": "ANY",
        "version_list": "ANY",
    }

    def layout(self):
        cmake_layout(self)

    def _as_list(self, opt_name, default_semicolon):
        """Return a semicolon separated string suitable for CMake from a user option.
        If option is "ANY" use the upstream defaults passed in."""
        val = str(getattr(self.options, opt_name))
        if val.upper() == "ANY":
            return default_semicolon
        # user supplies comma or semicolon separated list; normalize to semicolons
        parts = [p.strip() for p in val.replace(";", ",").split(",") if p.strip()]
        return ";".join(parts) if parts else default_semicolon

    def generate(self):
        tc = CMakeToolchain(self)
        # Upstream default sets in CMakeLists.txt
        default_versions = "128;256;v13"
        default_algs = "asconaead128;asconhash256;asconxof128;asconcxof128;asconaeadxof128;asconmacv13;asconprfv13;asconprfsv13"
        default_impls = "ref;opt64;opt64_lowsize;opt32;opt32_lowsize;bi32;bi32_lowsize;bi32_lowreg;esp32;opt8;opt8_lowsize;bi8"

        tc.variables["VERSION_LIST"] = self._as_list("version_list", default_versions)
        tc.variables["ALG_LIST"] = self._as_list("alg_list", default_algs)
        tc.variables["IMPL_LIST"] = self._as_list("impl_list", default_impls)

        # Disable tests by supplying an empty list when not requested.
        if self.options.with_tests:
            # keep upstream default (uses DEFAULT_TESTS from CMakeLists) -> leave TEST_LIST unset
            pass
        else:
            tc.variables["TEST_LIST"] = ""  # empty to skip creating executables
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="ascon-c")
        cmake.build()

    def package(self):
        # License
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        # Headers (all .h headers from source tree)
        include_dst = os.path.join(self.package_folder, "include")
        copy(self, "*.h", dst=include_dst, src=os.path.join(self.source_folder, "ascon-c"), keep_path=True)
        # Libraries
        lib_dst = os.path.join(self.package_folder, "lib")
        for pattern in ("*.a", "*.lib", "*.so", "*.dylib", "*.dll"):
            copy(self, pattern, dst=lib_dst, src=self.build_folder, keep_path=False)

    def package_info(self):
        # Collect all produced library names. Order doesn't matter much; adjust if needed.
        self.cpp_info.libs = collect_libs(self)
        # Provide a root include path so consumers can include directly algorithm headers.
        # Upstream libraries added their own paths but for consumers we just expose whole tree.
        # Users must pick the correct header path, e.g., crypto_aead/asconaead128/ref/api.h etc.

        # No system libs or defines required by default; toolchain flags handled by consumer.
        # Could add components here later if fine-grained linking is needed.
        pass

