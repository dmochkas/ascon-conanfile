from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import get, copy, collect_libs
from conan.errors import ConanException, ConanInvalidConfiguration
import os


class AsconConanRecipe(ConanFile):
    name = "ascon"
    # Adjust version as appropriate (could be synchronized with upstream tag)
    version = "1.0.0"
    license = "CC0-1.0"
    url = "https://github.com/ascon/ascon-c"
    description = "Reference, optimized and masked C/ASM implementations of Ascon (NIST SP 800-232)"
    topics = ("cryptography", "ascon", "aead", "hash", "mac", "prf")
    settings = "os", "arch", "compiler", "build_type"
    package_type = "library"

    # Comma separated lists to stay user friendly for CLI overrides.
    options = {
        "fPIC": [True, False],
        "shared": [True, False],
        "with_tests": [True, False],
        "with_asconaead128": [True, False],
        "with_asconhash256": [True, False],
        "with_asconxof128": [True, False],
        "with_asconcxof128": [True, False],
        "with_asconaeadxof128": [True, False],
        "with_asconmacv13": [True, False],
        "with_asconprfv13": [True, False],
        "with_asconprfsv13": [True, False],
        "optimized": ["size", "speed"]
    }

    default_options = {
        "fPIC": True,
        "shared": False,
        "with_tests": False,
        "with_asconaead128": True,
        "with_asconhash256": True,
        "with_asconxof128": False,
        "with_asconcxof128": False,
        "with_asconaeadxof128": False,
        "with_asconmacv13": False,
        "with_asconprfv13": False,
        "with_asconprfsv13": False,
        "optimized": "speed"
    }

    def source(self):
        # Please, be aware that using the head of the branch instead of an immutable tag
        # or commit is a bad practice and not allowed by Conan
        get(self, "https://github.com/ascon/ascon-c/archive/refs/heads/main.zip",
                  strip_root=True)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def config(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)

        algs = ';'.join((k[5:] for k, v in self.options.items() if k.startswith("with_ascon") and getattr(self.options, k) == True))
        self.output.info(f"Configuring the following algorithms: {algs}")

        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration(f"Unsupported architecture {self.settings.arch}")

        impl = "opt64" + ("_lowsize" if self.options.optimized == "size" else "")

        tc.variables["ALG_LIST"] = algs
        tc.variables["IMPL_LIST"] = impl
        if not self.options.with_tests:
            tc.variables["TEST_LIST"] = ""

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
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
        self.cpp_info.libs = collect_libs(self)
