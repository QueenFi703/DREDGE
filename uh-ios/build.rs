// Build script for µH-iOS cxx bindings
//
// This build script compiles the C++ bridge for Hypervisor.framework integration

fn main() {
    // Configure cxx bridge
    cxx_build::bridge("src/hvf.rs")
        .file("src/hvf_bridge.cpp")
        .flag_if_supported("-std=c++17")
        .compile("uh_ios_hvf");

    // Link against Hypervisor.framework on macOS/iOS
    #[cfg(target_os = "macos")]
    {
        println!("cargo:rustc-link-lib=framework=Hypervisor");
    }
    
    #[cfg(target_os = "ios")]
    {
        println!("cargo:rustc-link-lib=framework=Hypervisor");
    }

    // Rerun if bridge changes
    println!("cargo:rerun-if-changed=src/hvf.rs");
    println!("cargo:rerun-if-changed=src/hvf_bridge.cpp");
    println!("cargo:rerun-if-changed=src/hvf_bridge.h");
}
