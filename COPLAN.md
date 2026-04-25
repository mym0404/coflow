# Coplan Interaction Sequence

This document maps the runtime interaction order for `coplan`.
The root agent must treat `co flow` stdout YAML as the control contract and keep the planning flow thin.

```mermaid
sequenceDiagram
  participant User as "user"
  participant Root as "root agent"
  participant Co as "co flow"
  participant Sub as "subagent"

  User->>Root: [유저] planning request
  Root->>Co: [추론기계] co flow init --plan-id ... --title ...
  Co->>Co: [기계] create exec.yaml and initial bundle files
  Co-->>Root: [기계] stdout YAML: root_action=continue_flow

  Root->>Co: [추론기계] co flow next
  Co->>Co: [기계] read interview/status/context
  Co->>Sub: [기계] launch interview/scoring agents when needed
  Sub-->>Co: [추론형식] schema-bound JSON
  Co->>Co: [기계] record facts, score ambiguity, close gates when ready
  Co-->>Root: [기계] stdout YAML: root_action=ask_user

  Root->>User: [추론기계] ask exact root_action.question
  User-->>Root: [유저] answer
  Root->>Co: [추론기계] co flow respond --stdin
  Co->>Co: [기계] record answer and continue internal interview loop

  Co->>Sub: [기계] bundle_author when interview closes
  Sub-->>Co: [추론형식] draft, plan, tasks JSON
  Co->>Co: [기계] write bundle files and validate
  par contract review
    Co->>Sub: [기계] launch contract_reviewer
    Sub-->>Co: [추론형식] PASS or FAIL JSON
  and verification review
    Co->>Sub: [기계] launch verification_reviewer
    Sub-->>Co: [추론형식] PASS or FAIL JSON
  end
  Co->>Co: [기계] repair through bundle_author if review fails
  Co-->>Root: [기계] stdout YAML: root_action=present_draft

  Root->>User: [추론기계] present exact root_action.draft
  User-->>Root: [유저] approval or feedback
  Root->>Co: [추론기계] co flow respond --stdin
  Co->>Sub: [기계] classify feedback if needed
  Co->>Co: [기계] re-enter interview or approve/finalize
  Co-->>Root: [기계] stdout YAML: execute_task, ask_user, or present_draft
```

## Label Meaning

- `[기계]`: code-executed deterministic work such as file read/write, schema validation, state transition, subprocess launch, or stdout emission.
- `[추론기계]`: root-agent action that calls `co flow` or transports exact user-visible content from `root_action`.
- `[유저]`: user-authored request, answer, feedback, or approval.
- `[추론형식]`: AI judgment constrained to a required output shape such as JSON schema.
