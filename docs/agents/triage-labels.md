# Triage labels

The local tracker stores triage roles in the ticket's single `Status:` line.

| Skill role | Local status | Meaning |
| --- | --- | --- |
| needs-triage | needs-triage | Maintainer evaluation required |
| needs-info | needs-info | More information required from the reporter |
| ready-for-agent | ready-for-agent | Fully specified for agent implementation |
| ready-for-human | ready-for-human | Requires human implementation |
| wontfix | wontfix | Will not be actioned |

Use these strings when a skill asks to apply a triage label. Implementation
issues also carry `Category: bug` or `Category: enhancement`.

`claimed` and `resolved` are execution statuses, not additional triage roles;
their transitions and dependency rules are in [issue-tracker.md](issue-tracker.md).
Record the reason for a status change in the ticket's Comments or Answer section.
