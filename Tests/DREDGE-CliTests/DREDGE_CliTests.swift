import XCTest
@testable import DREDGE_Cli

final class DREDGE_CliTests: XCTestCase {
    func testExample() throws {
        // This is a placeholder test to satisfy Swift Package Manager
        XCTAssertTrue(true, "Basic test passes")
    }
    
    func testMainExists() throws {
        // Verify the module can be imported and has expected version
        XCTAssertEqual(DREDGECli.version, "0.1.0")
    }
}
