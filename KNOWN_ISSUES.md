# Known Issues

## MPV input.conf Validation Error

**Status:** Known Issue - Not Fixed  
**Severity:** High - Blocks installation of mpv-ultra-5090 package  
**Date Identified:** 2025-11-27

### Problem

The MPV config validator (`injekt/business/validator.py`) incorrectly rejects valid `input.conf` syntax, causing installation to fail with validation errors.

### Error Output

```
✗ Installation failed: Validation errors in assets\packages\mpv-ultra-5090\configs\input.conf:
Line 6: Invalid syntax: 'SPACE       cycle pause'
Line 7: Invalid syntax: 'ENTER       cycle pause'
Line 8: Invalid syntax: 'LEFT        seek -5'
...
```

### Root Cause

The validator is using overly strict regex patterns that don't match MPV's actual `input.conf` syntax. MPV's input.conf format allows:
- Multiple spaces/tabs between key and command
- Various key names (SPACE, ENTER, LEFT, RIGHT, UP, DOWN, etc.)
- Complex commands with arguments and quotes

The current validator pattern likely expects a specific format that doesn't match real-world MPV configs.

### Affected Files

- `injekt/business/validator.py` - MPV config validation logic
- `assets/packages/mpv-ultra-5090/configs/input.conf` - Valid MPV config being rejected

### Workaround

None currently available. Installation is blocked.

### Recommended Fix

1. Review MPV's official input.conf documentation
2. Update the regex pattern in `ConfigValidatorImpl.validate_mpv_config()` to properly handle:
   - Flexible whitespace between key and command
   - All valid MPV key names
   - Command syntax with arguments and quotes
3. Consider making validation more lenient or optional for input.conf files
4. Add comprehensive test cases for various valid input.conf formats

### Related Code

See `injekt/business/validator.py` around the MPV config validation section.

### Notes for Next Developer

- The input.conf file being rejected is actually valid MPV syntax
- This is a validator bug, not a config file issue
- Consider whether strict validation is necessary for input.conf or if it should be skipped
- May want to add a `--skip-validation` flag as a temporary workaround
