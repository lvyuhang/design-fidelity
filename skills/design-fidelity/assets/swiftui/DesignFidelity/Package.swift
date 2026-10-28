// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "DesignFidelity",
    platforms: [.iOS(.v16)],
    products: [.library(name: "DesignFidelity", targets: ["DesignFidelity"])],
    targets: [.target(name: "DesignFidelity")]
)
