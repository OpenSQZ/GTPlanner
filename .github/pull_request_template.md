# Pull Request

## Choose the Right Template

For better organization and review process, please use the appropriate specialized template:

- **📦 Prefab Contribution**: [Use Prefab Template](?template=prefab.md) - For adding/updating prefabs in community-prefabs.json
- **🔧 API Tool Contribution**: [Use API Tool Template](?template=api_tool.md)
- **📦 Python Package Tool**: [Use Python Package Template](?template=python_package_tool.md)
- **📚 Documentation Changes**: [Use Documentation Template](?template=documentation.md)
- **🛠️ General Changes**: [Use General Template](?template=general.md)

---

## Description

**Summary of changes:**
Provide a clear and concise description of what this PR does.

**Related issue(s):**
Fixes #(issue number) or Closes #(issue number)

**Motivation and context:**
Why is this change required? What problem does it solve?

## Type of Change

Please mark the relevant option(s):

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test addition or improvement
- [ ] 🔨 Build/CI changes
- [ ] 🎨 Code style/formatting changes

## Changes Made

**Files modified:**
- `file1.py` - Description of changes
- `file2.py` - Description of changes

**Key changes:**
- Change 1: Description
- Change 2: Description
- Change 3: Description

## Testing Performed

**Manual testing completed:**
- [ ] CLI functionality tested
- [ ] API endpoints tested (if applicable)
- [ ] MCP service tested (if applicable)
- [ ] Error handling tested
- [ ] Edge cases tested

**Test commands used:**
```bash
# List the specific commands you used to test
uv run python main.py
# Add other test commands here
```

**Test scenarios covered:**
1. Scenario 1: Description and result
2. Scenario 2: Description and result
3. Scenario 3: Description and result

**Sample input/output:**
```
Input: "Your test input here"
Output: "Expected output here"
```

## Environment Tested

- **Python version**: [e.g., 3.10.5]
- **Operating System**: [e.g., Windows 11, macOS 13.0, Ubuntu 22.04]
- **Package manager**: [e.g., uv, pip]
- **LLM Provider**: [e.g., OpenAI, Anthropic]

## Breaking Changes

**Are there any breaking changes?**
- [ ] No breaking changes
- [ ] Yes, breaking changes (describe below)

**If yes, describe the breaking changes:**
- Change 1: What breaks and how to migrate
- Change 2: What breaks and how to migrate

## Documentation

- [ ] Code comments added/updated
- [ ] README.md updated (if needed)
- [ ] CONTRIBUTING.md updated (if needed)
- [ ] API documentation updated (if applicable)
- [ ] No documentation changes needed

## Dependencies

**New dependencies added:**
- [ ] No new dependencies
- [ ] New dependencies added (list below)

**If new dependencies were added:**
- `dependency-name==version` - Reason for adding

## Performance Impact

- [ ] No performance impact
- [ ] Performance improvement
- [ ] Potential performance regression (explain below)

**Performance notes:**
Describe any performance considerations or measurements.

## Security Considerations

- [ ] No security implications
- [ ] Security improvements
- [ ] Potential security concerns (explain below)

**Security notes:**
Describe any security-related changes or considerations.

## Reviewer Checklist

**For reviewers to complete:**

**Code Quality:**
- [ ] Code follows project style guidelines
- [ ] Code is well-documented and readable
- [ ] Error handling is appropriate
- [ ] No obvious bugs or issues

**Functionality:**
- [ ] Changes work as described
- [ ] No regressions in existing functionality
- [ ] Edge cases are handled appropriately
- [ ] Integration points work correctly

**Testing:**
- [ ] Manual testing is adequate
- [ ] Test scenarios cover the changes
- [ ] Error conditions are tested
- [ ] Performance is acceptable

**Documentation:**
- [ ] Code is properly documented
- [ ] User-facing documentation is updated
- [ ] Breaking changes are clearly documented

## Additional Notes

**Anything else reviewers should know:**
Add any additional context, concerns, or notes for reviewers.

**Follow-up tasks:**
List any tasks that should be done after this PR is merged.

---

**Checklist for submitter:**
- [ ] I have tested these changes thoroughly
- [ ] I have updated documentation as needed
- [ ] I have followed the project's coding standards
- [ ] I have checked for any breaking changes
- [ ] I have linked related issues
- [ ] I am ready for code review
