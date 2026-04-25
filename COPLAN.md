# Coplan Interaction Sequence

This document maps the runtime interaction order for `coplan`.
The root agent must treat `co` stdout YAML as the control contract and keep the planning flow thin.

```mermaid
sequenceDiagram
  participant User as "user"
  participant Root as "root agent"
  participant Co as "co cli"
  participant Sub as "subagent"

  User->>Root: [유저] planning request
  Root->>Co: [추론기계] co planner init --plan-id ... --title ...
  Co->>Co: [기계] create exec.yaml and initial bundle files
  Co-->>Root: [기계] stdout YAML: required_action + next_command

  Root->>Root: [추론] inspect target repo and summarize code facts
  Root->>Co: [추론기계] co planner interview ask-next
  Co->>Co: [기계] read interview/status/context
  Co->>Sub: [기계] launch codex exec with prompt + JSON schema
  Sub-->>Co: [추론형식] next interview action JSON

  alt ask_user
    Co->>Co: [기계] write pending_user_question
    Co-->>Root: [기계] stdout YAML with pending_user_question
    Root->>User: [추론기계] ask exact pending question
    User-->>Root: [유저] answer
    Root->>Co: [추론기계] co planner interview record ...
    Co->>Co: [기계] append round, clear pending question, append event
  else record_fact
    Co->>Co: [기계] append code_fact or research_confirmation round
    Co-->>Root: [기계] stdout YAML with next_command
  else ready_for_score
    Co-->>Root: [기계] stdout YAML with score next_command
  end

  Root->>Co: [추론기계] co planner interview score --mode auto
  Co->>Co: [기계] read interview rounds
  Co->>Sub: [기계] launch ambiguity scorer
  Sub-->>Co: [추론형식] clarity component JSON
  Co->>Co: [기계] compute ambiguity, write score, append event
  Co-->>Root: [기계] stdout YAML: ready state or follow-up

  loop until interview close gates pass
    Root->>Co: [추론기계] ask-next, record, score, track close, closure-check, blocker commands
    Co->>Co: [기계] validate tracks, source routes, blockers, freshness, ambiguity gates
    Co-->>Root: [기계] stdout YAML: required_action
  end

  Root->>Co: [추론기계] co planner interview close --summary ...
  Co->>Co: [기계] mark interview closed and append event
  Co-->>Root: [기계] stdout YAML: generate-skeleton next_command

  Root->>Co: [추론기계] co planner generate-skeleton
  Co->>Co: [기계] build planning_context.yaml and enforce context gate
  Co->>Co: [기계] write draft.md, plan.yaml, tasks.yaml, status task state
  Co-->>Root: [기계] stdout YAML: planning_context_file + patch allowed files

  Root->>Root: [추론] read planning_context.yaml and patch draft.md, plan.yaml, tasks.yaml only
  Root->>Co: [추론기계] co planner validate
  Co->>Co: [기계] validate draft, plan, tasks, interview, status
  Co-->>Root: [기계] stdout YAML: run pre-draft review

  Root->>Co: [추론기계] co planner review run --stage pre-draft
  Co->>Co: [기계] read bundle and compute review context
  par contract review
    Co->>Sub: [기계] launch contract_reviewer
    Sub-->>Co: [추론형식] PASS or FAIL JSON
  and verification review
    Co->>Sub: [기계] launch verification_reviewer
    Sub-->>Co: [추론형식] PASS or FAIL JSON
  end
  Co->>Co: [기계] write review state, notes, events, fingerprint on PASS
  Co-->>Root: [기계] stdout YAML: show draft or patch valid findings

  alt review FAIL
    Root->>Root: [추론] patch valid reviewer findings in allowed files
    Root->>Co: [추론기계] rerun validate and pre-draft review
  else review PASS
    Root->>Co: [추론기계] co show --file draft
    Co->>Co: [기계] read draft.md
    Co-->>Root: [기계] raw Markdown draft
    Root->>User: [추론기계] present draft for review
  end

  alt user requests meaning change
    User-->>Root: [유저] draft feedback
    Root->>Co: [추론기계] reopen affected interview track and create/record question
    Co->>Co: [기계] update interview state and reset review freshness
    Root->>Co: [추론기계] rescore, close gates, regenerate or patch impacted files
  else user approves
    User-->>Root: [유저] approval
    Root->>Co: [추론기계] co planner approve-draft --comment ...
    Co->>Co: [기계] set phase=planning and append approval event
  end

  Root->>Co: [추론기계] co planner validate
  Co->>Co: [기계] validate finalized bundle contract
  Co-->>Root: [기계] stdout YAML: finalize when gates pass
  Root->>Co: [추론기계] co planner finalize
  Co->>Co: [기계] require approved draft, fresh review, valid files and set phase=ready_for_exec
  Co-->>Root: [기계] stdout YAML: switch to coexec and run co exec status
```

## Label Meaning

- `[기계]`: code-executed deterministic work such as file read/write, schema validation, state transition, subprocess launch, or stdout emission.
- `[추론기계]`: root-agent action that calls a command or transports an exact prompt because the AI followed `co` guidance.
- `[유저]`: user-authored request, answer, feedback, or approval.
- `[추론]`: free-form AI judgment or authoring by the root agent.
- `[추론형식]`: AI judgment constrained to a required output shape such as JSON schema.
