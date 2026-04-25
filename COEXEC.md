# Coexec 흐름도

이 문서는 `coexec`가 승인된 plan bundle을 current task 단위로 실행하는 흐름을 보여주는 사용자용 문서다.
그래프의 초점은 `co.py flow`가 task 선택과 completion을 관리하고, root agent가 구현과 검증 실행을 맡는 방식이다.

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
    Root->>Shell: [추론기계] task verification command 실행
    Shell-->>Root: [기계] output과 exit code
    Root->>Co: [추론기계] co.py flow evidence --stdin
    Co->>Co: [기계] evidence artifact와 manifest 기록
    alt evidence 성공과 completion gate 통과
      Co->>Co: [기계] task Done 처리
      alt 다음 ready task 있음
        Co->>Co: [기계] 다음 ready task claim
        Co-->>Root: [기계] root_action=execute_task
      else 모든 task와 final verification 완료
        Co->>Co: [기계] execution finish
        Co-->>Root: [기계] root_action=report_complete
      end
    else evidence 실패
      Co->>Co: [기계] task Doing 유지와 risk note 기록
      Co-->>Root: [기계] root_action=repair_task
      Root->>Root: [추론기계] current task 범위 수정
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
  Verify["[추론기계] task verification 실행"]
  Evidence{"[기계] verification accepted?"}
  Blocked{"[추론기계] contract 변경 필요?"}
  Repair["[추론기계] current task 수정"]
  Halt(["[추론기계] halt 보고"])
  Done["[기계] task done 처리"]
  More{"[기계] 남은 approved task?"}
  Complete(["[추론기계] completion 보고"])

  Start --> Handoff
  Handoff --> Task
  Task --> Implement
  Implement --> Verify
  Verify --> Evidence
  Evidence -->|no| Blocked
  Blocked -->|yes| Halt
  Blocked -->|no| Repair
  Repair --> Verify
  Evidence -->|yes| Done
  Done --> More
  More -->|yes| Task
  More -->|no| Complete

  linkStyle default stroke:#616161,stroke-width:1.5px
  linkStyle 0 stroke:#2e7d32,stroke-width:2px
  linkStyle 1,3,4,6,7,8,12 stroke:#1565c0,stroke-width:2px
```

## Label Meaning

- `[기계]`: state transition, evidence write, task claim, task completion, halt, finish처럼 코드로 실행되는 단계.
- `[추론기계]`: root agent가 source를 수정하거나 verification을 실행하거나 `co.py flow`를 호출하거나 반환된 action을 보고하는 단계.
- `[유저]`: plan 승인처럼 사용자가 흐름을 시작시키는 입력.
- Flowchart edge 색상은 같은 역할을 따른다. blue는 `[추론기계]`, gray는 `[기계]`, green은 `[유저]`다.
