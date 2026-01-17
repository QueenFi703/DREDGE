// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "DREDGE-Cli",
    platforms: [
        .macOS(.v12),
        .iOS(.v15)
    ],
    products: [
        // Executable CLI tool
        .executable(
            name: "dredge-cli",
            targets: ["DREDGECli"]
        ),
        // iOS MVP App library
        .library(
            name: "DREDGEMVPApp",
            targets: ["DREDGEMVPApp"]
        )
    ],
    targets: [
        // CLI executable target (from swift/Sources/main.swift)
        .executableTarget(
            name: "DREDGECli",
            path: "swift/Sources"
        ),
        // iOS MVP App library target
        .target(
            name: "DREDGEMVPApp",
            dependencies: [],
            path: "swift/DREDGE_MVP_App",
            resources: [
                .process("AboutStrings.strings")
            ]
        ),
        // Test target
        .testTarget(
            name: "DREDGE-CliTests",
            dependencies: ["DREDGECli"],
            path: "swift/Tests/DREDGE-CliTests"
        )
    ]
)
