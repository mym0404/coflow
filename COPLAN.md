# Coplan Runtime Graphs

This document maps the runtime flow for `coplan`.
The root agent must treat `co flow` stdout YAML as the control contract and only perform the returned `root_action`.

## Sequence Diagram

```mermaid
sequenceDiagram
  participant User as user
  participant Root as root agent
  participant Co as co flow
  participant Agent as Codex CLI agent

  User->>Root: [유저] planning request
  Root->>Co: [추론기계] co flow init --plan-id ... --title ...
  Co->>Co: [기계] create exec.yaml and initial bundle files
  Co-->>Root: [기계] root_action=continue_flow

  loop until interview reaches a root boundary
    Root->>Co: [추론기계] co flow next or co flow respond --stdin
    Co->>Co: [기계] read interview, status, and context
    alt user answer is needed
      Co-->>Root: [기계] root_action=ask_user
      Root->>User: [추론기계] ask root_action.question exactly
      User-->>Root: [유저] answer
      Root->>Co: [추론기계] co flow respond --stdin
      Co->>Co: [기계] record answer and clear pending question
    else internal step is possible
      Co->>Agent: [기계] ask-next or ambiguity scorer
      Agent-->>Co: [추론형식] schema-bound JSON
      Co->>Co: [기계] record fact, score ambiguity, or close interview gates
    end
  end

  Co->>Agent: [기계] bundle_author
  Agent-->>Co: [추론형식] draft.md, plan.yaml, tasks.yaml JSON
  Co->>Co: [기계] write and validate bundle files

  loop until pre-draft review passes
    par contract review
      Co->>Agent: [기계] contract_reviewer
      Agent-->>Co: [추론형식] PASS or FAIL JSON
    and verification review
      Co->>Agent: [기계] verification_reviewer
      Agent-->>Co: [추론형식] PASS or FAIL JSON
    end
    alt any reviewer fails
      Co->>Agent: [기계] bundle_author with findings
      Agent-->>Co: [추론형식] revised bundle JSON
      Co->>Co: [기계] rewrite and validate bundle files
    else both reviewers pass
      Co-->>Root: [기계] root_action=present_draft
    end
  end

  Root->>User: [추론기계] present root_action.draft exactly
  User-->>Root: [유저] approval or feedback
  Root->>Co: [추론기계] co flow respond --stdin
  Co->>Agent: [기계] draft feedback classifier when needed
  Agent-->>Co: [추론형식] approval, wording_change, or meaning_change JSON
  alt approval
    Co->>Co: [기계] approve, finalize, start execution, claim task
    Co-->>Root: [기계] root_action=execute_task
  else wording change
    Co->>Agent: [기계] bundle_author with wording feedback
    Co->>Co: [기계] rerun validation and parallel review
    Co-->>Root: [기계] root_action=present_draft
  else meaning change
    Co->>Co: [기계] reopen track, record feedback answer, rescore
    Co-->>Root: [기계] root_action=ask_user or present_draft
  end
```

## Flowchart

```mermaid
flowchart TD
  subgraph Legend["Edge Color Legend"]
    LUser["[유저] user input edge: green"]
    LRoot["[추론기계] root transport/action edge: blue"]
    LMachine["[기계] deterministic CLI/runtime edge: gray"]
    LReason["[추론형식] schema-bound AI judgment edge: yellow"]
  end

  Start(["[유저] planning request"])
  Init["[추론기계] root runs co flow init"]
  RootAction{"[기계] root_action.type"}

  Start --> Init --> RootAction

  RootAction -->|continue_flow| Next["[추론기계] root runs co flow next"]
  RootAction -->|ask_user| AskUser["[추론기계] ask root_action.question exactly"]
  AskUser --> UserAnswer["[유저] answer"]
  UserAnswer --> Respond["[추론기계] root pipes to co flow respond --stdin"]
  RootAction -->|present_draft| PresentDraft["[추론기계] present root_action.draft exactly"]
  PresentDraft --> UserFeedback["[유저] approval or feedback"]
  UserFeedback --> Respond
  RootAction -->|execute_task| ExecHandoff(["[추론기계] switch to coexec"])
  RootAction -->|report_halt| Halt(["[추론기계] report halt"])
  RootAction -->|report_complete| Complete(["[추론기계] report complete"])

  Next --> Phase{"[기계] current phase"}
  Respond --> Phase

  Phase -->|drafting| IRead
  Phase -->|draft_review| FClassify
  Phase -->|planning or ready_for_exec| EStart

  subgraph Interview["[기계] interview iterator inside co flow"]
    direction TD
    IRead["read interview/status/context"]
    IPending{"pending user question?"}
    IClosure{"closure gates pass?"}
    IAskNext["[추론형식] ask-next agent"]
    IScore["[추론형식] ambiguity scorer"]
    IFact["record repo or research fact"]
    IQuestion["create pending_user_question"]
    IClose["close tracks and closure checks"]
    IEmitAsk["emit root_action=ask_user"]

    IRead --> IPending
    IPending -->|yes| IEmitAsk
    IPending -->|no| IClosure
    IClosure -->|yes| IClose
    IClosure -->|no| IAskNext
    IAskNext -->|record_fact| IFact --> IScore --> IRead
    IAskNext -->|ready_for_score| IScore --> IRead
    IAskNext -->|ask_user| IQuestion --> IEmitAsk
  end

  IEmitAsk --> RootAction
  IClose --> AAuthor

  subgraph Author["[기계] bundle authoring and review loop inside co flow"]
    direction TD
    AAuthor["[추론형식] bundle_author returns draft, plan, tasks"]
    AValidate["[기계] validate bundle schema and gates"]
    AReviewFork{{"[기계] run reviewers in parallel"}}
    AContract["[추론형식] contract_reviewer"]
    AVerification["[추론형식] verification_reviewer"]
    AReviewJoin{{"[기계] join review results"}}
    APass{"both reviewers PASS?"}
    ARewrite["[기계] feed findings back to bundle_author"]
    AEmitDraft["emit root_action=present_draft"]

    AAuthor --> AValidate --> AReviewFork
    AReviewFork --> AContract --> AReviewJoin
    AReviewFork --> AVerification --> AReviewJoin
    AReviewJoin --> APass
    APass -->|no| ARewrite --> AAuthor
    APass -->|yes| AEmitDraft
  end

  AEmitDraft --> RootAction

  subgraph Feedback["[기계] draft feedback handling inside co flow"]
    direction TD
    FClassify{"[추론형식] approval, wording change, or meaning change?"}
    FApprove["[기계] approve draft and finalize"]
    FWording["[기계] rewrite wording through bundle_author"]
    FMeaning["[기계] reopen affected interview track and record feedback"]
    EStart["[기계] start execution and claim first ready task"]
    FEmitExecute["emit root_action=execute_task"]

    FClassify -->|approval| FApprove --> EStart
    FClassify -->|wording_change| FWording --> AAuthor
    FClassify -->|meaning_change| FMeaning --> IRead
    EStart --> FEmitExecute
  end

  FEmitExecute --> RootAction

  linkStyle default stroke:#616161,stroke-width:1.5px
  linkStyle 0,4,7 stroke:#2e7d32,stroke-width:2px
  linkStyle 2,3,5,6,8,9,10,11 stroke:#1565c0,stroke-width:2px
  linkStyle 15,21,22,23,24,25,26,27,30,31,33,34,35,36,39,42,44,45,46 stroke:#f9a825,stroke-width:2px
```

## Label Meaning

- `[기계]`: code-executed deterministic work such as file read/write, schema validation, state transition, subprocess launch, or stdout emission.
- `[추론기계]`: root-agent action that calls `co flow` or transports exact user-visible content from `root_action`.
- `[유저]`: user-authored request, answer, feedback, or approval.
- `[추론형식]`: AI judgment constrained to a required output shape such as JSON schema.
- Flowchart edge colors match the same roles: green for `[유저]`, blue for `[추론기계]`, gray for `[기계]`, and yellow for `[추론형식]`.
