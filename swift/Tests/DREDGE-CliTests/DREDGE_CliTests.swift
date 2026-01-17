import XCTest
@testable import DREDGECli

final class DREDGE_CliTests: XCTestCase {
    func testVersion() {
        XCTAssertEqual(DREDGECli.version, "0.2.0")
    }
    
    func testVersionFormat() {
        // Verify version follows semantic versioning format (X.Y.Z)
        let versionComponents = DREDGECli.version.split(separator: ".")
        XCTAssertEqual(versionComponents.count, 3, "Version should have 3 components (major.minor.patch)")
        
        // Each component should be a valid number
        for component in versionComponents {
            XCTAssertNotNil(Int(component), "Version component '\(component)' should be a number")
        }
    }
    
    func testTagline() {
        XCTAssertFalse(DREDGECli.tagline.isEmpty, "Tagline should not be empty")
        XCTAssertEqual(DREDGECli.tagline, "Digital memory must be human-reachable.")
    }
    
    func testRunMethod() {
        // Test that run method exists and is callable
        // This test verifies the method can be invoked without crashing
        XCTAssertNoThrow(DREDGECli.run())
    }
}

// MARK: - String Theory Tests

final class StringTheoryTests: XCTestCase {
    func testStringTheoryCreation() throws {
        let stringTheory = StringTheory(dimensions: 10, length: 1.0)
        XCTAssertEqual(stringTheory.dimensions, 10)
        XCTAssertEqual(stringTheory.length, 1.0)
    }
    
    func testVibrationalMode() throws {
        let stringTheory = StringTheory()
        
        // Test at x=0 (should be 0)
        let mode1_0 = stringTheory.vibrationalMode(n: 1, x: 0.0)
        XCTAssertEqual(mode1_0, 0.0, accuracy: 1e-10)
        
        // Test at x=0.5 (should be maximum for n=1)
        let mode1_mid = stringTheory.vibrationalMode(n: 1, x: 0.5)
        XCTAssertEqual(mode1_mid, 1.0, accuracy: 1e-10)
        
        // Test at x=1.0 (should be 0)
        let mode1_1 = stringTheory.vibrationalMode(n: 1, x: 1.0)
        XCTAssertEqual(mode1_1, 0.0, accuracy: 1e-10)
    }
    
    func testEnergyLevel() throws {
        let stringTheory = StringTheory(length: 1.0)
        
        let e1 = stringTheory.energyLevel(n: 1)
        let e2 = stringTheory.energyLevel(n: 2)
        
        // Energy should be proportional to mode number
        XCTAssertEqual(e2, 2.0 * e1, accuracy: 1e-10)
    }
    
    func testModeSpectrum() throws {
        let stringTheory = StringTheory()
        let spectrum = stringTheory.modeSpectrum(maxModes: 10)
        
        XCTAssertEqual(spectrum.count, 10)
        
        // Energy should increase with mode number
        for i in 0..<(spectrum.count - 1) {
            XCTAssertLessThan(spectrum[i], spectrum[i + 1])
        }
    }
    
    func testInvalidVibrationalMode() throws {
        let stringTheory = StringTheory()
        
        // Invalid mode number (n < 1) should return 0
        let invalidMode = stringTheory.vibrationalMode(n: 0, x: 0.5)
        XCTAssertEqual(invalidMode, 0.0)
        
        // Invalid position (x > 1) should return 0
        let invalidPosition = stringTheory.vibrationalMode(n: 1, x: 1.5)
        XCTAssertEqual(invalidPosition, 0.0)
    }
}

// MARK: - MCP Client Tests

final class MCPClientTests: XCTestCase {
    func testMCPClientCreation() throws {
        let client = MCPClient(serverURL: "http://localhost:3002")
        XCTAssertEqual(client.serverURL, "http://localhost:3002")
    }
    
    func testMCPClientDefaultURL() throws {
        let client = MCPClient()
        XCTAssertEqual(client.serverURL, "http://localhost:3002")
    }
}

// MARK: - Unified DREDGE Tests

final class UnifiedDREDGETests: XCTestCase {
    func testUnifiedDREDGECreation() throws {
        let unified = UnifiedDREDGE(dimensions: 10, serverURL: "http://localhost:3002")
        XCTAssertEqual(unified.stringTheory.dimensions, 10)
        XCTAssertEqual(unified.mcpClient.serverURL, "http://localhost:3002")
    }
    
    func testDefaultUnifiedDREDGE() throws {
        let unified = UnifiedDREDGE()
        XCTAssertEqual(unified.stringTheory.dimensions, 10)
        XCTAssertEqual(unified.mcpClient.serverURL, "http://localhost:3002")
    }
}

