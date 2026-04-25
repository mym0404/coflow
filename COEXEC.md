# Coexec Runtime Graphs

This document maps the runtime flow for `coexec`.
The root agent must execute only the current task returned by `co flow` and send verification output back through `co flow evidence`.

## Sequence Diagram

```mermaid
sequenceDiagram
  participant Root as root agent
  participant Co as co flow
  participant Shell as local shell

  Root->>Co: [추론기계] co flow next
  Co->>Co: [기계] start execution if ready_for_exec
  Co->>Co: [기계] claim first ready task if no current task
  Co-->>Root: [기계] root_action=execute_task

  loop until report_complete or report_halt
    Root->>Root: [추론기계] edit source within root_action.task only
    Root->>Shell: [추론기계] run task verification command
    Shell-->>Root: [기계] output and exit code
    Root->>Co: [추론기계] co flow evidence --stdin
    Co->>Co: [기계] record evidence artifact and manifest entry
    alt evidence succeeds and completion gate passes
      Co->>Co: [기계] mark task Done
      alt another task is ready
        Co->>Co: [기계] claim next ready task
        Co-->>Root: [기계] root_action=execute_task
      else all tasks and final verification are Done
        Co->>Co: [기계] finish execution
        Co-->>Root: [기계] root_action=report_complete
      end
    else evidence fails
      Co->>Co: [기계] keep task Doing and append risk note
      Co-->>Root: [기계] root_action=repair_task
      Root->>Root: [추론기계] repair within current task contract
    end
  end
```

## Flowchart

```mermaid
flowchart TD
  Start(["[추론기계] enter coexec"])
  Next["[추론기계] root runs co flow next"]
  Phase{"[기계] phase"}

  Start --> Next --> Phase

  Phase -->|ready_for_exec| StartExec["[기계] set phase=executing"]
  StartExec --> Phase
  Phase -->|executing| Current{"current_task exists?"}
  Phase -->|halted| EmitHalt["emit root_action=report_halt"]
  Phase -->|complete| EmitComplete["emit root_action=report_complete"]

  Current -->|yes| EmitExecute["emit root_action=execute_task"]
  Current -->|no| Ready{"ready task exists?"}
  Ready -->|yes| Claim["[기계] claim first ready task"]
  Claim --> EmitExecute
  Ready -->|no| Finish{"all tasks and final verification Done?"}
  Finish -->|yes| MarkComplete["[기계] finish execution"]
  MarkComplete --> EmitComplete
  Finish -->|no| HaltNeeded["[기계] no valid next execution boundary"]

  EmitExecute --> Implement["[추론기계] root edits only root_action.task"]
  Implement --> Verify["[추론기계] root runs verification command"]
  Verify --> Evidence["[추론기계] pipe output to co flow evidence"]
  Evidence --> EvidenceResult{"[기계] evidence success?"}

  EvidenceResult -->|false| Risk["[기계] record risk note and keep task Doing"]
  Risk --> EmitRepair["emit root_action=repair_task"]
  EmitRepair --> Repair["[추론기계] repair within current task contract"]
  Repair --> Verify

  EvidenceResult -->|true| Required{"required evidence now complete?"}
  Required -->|no| EmitExecute
  Required -->|yes| Done["[기계] mark current task Done and clear current_task"]
  Done --> Phase

  EmitHalt --> ReportHalt(["[추론기계] root reports halt"])
  EmitComplete --> ReportComplete(["[추론기계] root reports completion"])
  HaltNeeded --> FlowError(["[기계] emit flow error"])

  linkStyle default stroke:#616161,stroke-width:1.5px
  linkStyle 0,15,16,17,21,22,27,28 stroke:#1565c0,stroke-width:2px
```

## Label Meaning

- `[기계]`: code-executed deterministic work such as state transition, evidence write, task claim, task completion, halt, or finish.
- `[추론기계]`: root-agent action that edits source, runs verification, calls `co flow`, or reports a returned root action.
- Flowchart edge colors match the same roles: blue for `[추론기계]` and gray for `[기계]`.
