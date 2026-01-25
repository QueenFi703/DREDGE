## v0.1.7 - Dockerfile Optimization

### Changes
- Removed redundant `rm -rf /root/.cache/pip` commands from Dockerfile
- The `--no-cache-dir` flag already prevents pip from creating caches
- Kept necessary `/tmp/*` cleanup operations
- Results in cleaner, more honest Dockerfile

### Technical Details
- 6 redundant cache cleanup commands removed
- No functional changes to build process
- Smaller, more maintainable Dockerfile

**Full Changelog**: https://github.com/QueenFi703/DREDGE-Cli/compare/v0.1.6...v0.1.7
