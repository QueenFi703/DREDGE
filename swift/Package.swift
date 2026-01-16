// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "DREDGE-Cli",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(
            name: "dredge-cli",
            targets: ["DREDGECli"]
        )
    ],
    targets: [
        .executableTarget(
            name: "DREDGECli",
            path: "Sources"
        ),
        .testTarget(
            name: "DREDGE-CliTests",
            dependencies: ["DREDGECli"],
            path: "Tests/DREDGE-CliTests"
        )
    ]
)
