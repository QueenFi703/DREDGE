// DREDGE CLI - Command Line Interface
// Minimal entry point for the DREDGE CLI tool

import Foundation

let version = "0.1.4"

print("DREDGE CLI v\(version)")
print("Type 'help' for available commands")

// Basic command loop
while true {
    print("> ", terminator: "")
    guard let input = readLine()?.trimmingCharacters(in: .whitespaces) else {
        break
    }
    
    if input.isEmpty {
        continue
    }
    
    switch input.lowercased() {
    case "help":
        print("Available commands:")
        print("  help - Show this help message")
        print("  version - Show version information")
        print("  exit - Exit the CLI")
    case "version":
        print("DREDGE CLI v\(version)")
    case "exit", "quit":
        print("Goodbye!")
        exit(0)
    default:
        print("Unknown command: \(input)")
        print("Type 'help' for available commands")
    }
}
