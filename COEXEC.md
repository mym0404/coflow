# Coexec 흐름도

이 문서는 `coexec`가 승인된 plan bundle을 current task 단위로 실행하는 흐름을 보여주는 사용자용 문서다.
그래프의 초점은 `co.py flow`가 task 선택과 완료 전이를 관리하고, root agent가 구현, mechanical 검증, semantic self-review를 맡는 방식이다.

## Sequence Diagram

```mermaid
sequenceDiagram
  participant Root as root agent
  participant Co as co.py flow
  participant Shell as local shell

  Root->>Co: [추론기계] co.py flow next
  Co->>Co: [기계] ready_for_exec이면 execution 시작
  Co->>Co: [기계] current task가 없으면 ready task claim
  Co-->>Root: [기계] root_action=execute_task

  loop report_complete 또는 report_halt까지
    Root->>Root: [추론기계] current task 범위 구현
    Root->>Shell: [추론기계] mechanical command 실행
    Shell-->>Root: [기계] output과 exit code
    Root->>Co: [추론기계] co.py flow evidence --kind mechanical
    Co->>Co: [기계] mechanical evidence record 저장
    alt mechanical 실패
      Co-->>Root: [기계] root_action=repair_task
      Root->>Root: [추론기계] current task 범위 수정
    else mechanical 계속 진행
      Root->>Root: [추론기계] semantic self-review 수행
      Root->>Co: [추론기계] co.py flow evidence --kind semantic
      Co->>Co: [기계] semantic evidence record 저장
      alt semantic 실패
        Co-->>Root: [기계] root_action=repair_task
        Root->>Root: [추론기계] current task 범위 수정
      else 모든 required verification pass
        Root->>Co: [추론기계] co.py flow task-done --stdin
        Co->>Co: [기계] task Done 처리
        alt 다음 ready task 있음
          Co->>Co: [기계] 다음 ready task claim
          Co-->>Root: [기계] root_action=execute_task
        else 모든 task와 final verification 완료
          Co->>Co: [기계] execution finish
          Co-->>Root: [기계] root_action=report_complete
        end
      end
    end
  end
```

## Flowchart

```mermaid
flowchart TD
  Start(["[유저] plan 승인"])
  Handoff["[추론기계] execution 진입"]
  Task["[기계] approved task를 current로 지정"]
  Implement["[추론기계] current task 구현"]
  Mechanical["[추론기계] mechanical verification 실행"]
  MechanicalRecord["[기계] mechanical evidence 기록"]
  MechanicalFailed{"[기계] mechanical 실패?"}
  Semantic["[추론기계] semantic self-review"]
  SemanticRecord["[기계] semantic evidence 기록"]
  SemanticFailed{"[기계] semantic 실패?"}
  Blocked{"[추론기계] contract 변경 필요?"}
  Repair["[추론기계] current task 수정"]
  Halt(["[추론기계] halt 보고"])
  TaskDone["[추론기계] co.py flow task-done"]
  Done["[기계] task done 처리"]
  More{"[기계] 남은 approved task?"}
  Complete(["[추론기계] completion 보고"])

  Start --> Handoff
  Handoff --> Task
  Task --> Implement
  Implement --> Mechanical
  Mechanical --> MechanicalRecord
  MechanicalRecord --> MechanicalFailed
  MechanicalFailed -->|yes| Blocked
  MechanicalFailed -->|no| Semantic
  Semantic --> SemanticRecord
  SemanticRecord --> SemanticFailed
  SemanticFailed -->|yes| Blocked
  Blocked -->|yes| Halt
  Blocked -->|no| Repair
  Repair --> Mechanical
  SemanticFailed -->|no| TaskDone
  TaskDone --> Done
  Done --> More
  More -->|yes| Task
  More -->|no| Complete

  linkStyle default stroke:#616161,stroke-width:1.5px
  linkStyle 0 stroke:#2e7d32,stroke-width:2px
  linkStyle 1,3,4,5,6,7,9,10,11,12 stroke:#1565c0,stroke-width:2px
```

## Label Meaning

- `[기계]`: state transition, evidence record 저장, task claim, task completion, halt, finish처럼 코드로 실행되는 단계.
- `[추론기계]`: root agent가 source를 수정하거나 mechanical command를 실행하거나 semantic self-review를 수행하거나 `co.py flow`를 호출하는 단계.
- `[유저]`: plan 승인처럼 사용자가 흐름을 시작시키는 입력.
- Flowchart edge 색상은 같은 역할을 따른다. blue는 `[추론기계]`, gray는 `[기계]`, green은 `[유저]`다.
