> [!NOTE]
> 일단 내가 써봐야겟다

할거
1. who consumes evidences, notes
2. semantic verificaiton

> README.md 는 나중에 쓰자.

![](https://cdn.jsdelivr.net/gh/mym0404/ia2/20260429204106707.png)
![](https://cdn.jsdelivr.net/gh/mym0404/ia2/20260429204141692.png)
![](https://cdn.jsdelivr.net/gh/mym0404/ia2/20260429204158612.png)
![](https://cdn.jsdelivr.net/gh/mym0404/ia2/20260429204842725.png)

## Coplan

### Sequence Diagram

```mermaid
sequenceDiagram
  participant User as user
  participant Root as root agent
  participant Co as co.py flow
  participant Agent as Codex CLI agent

  User->>Root: [유저] planning 요청
  Root->>Co: [추론기계] co.py flow init --plan-id ... --title ... --stdin
  Co->>Co: [기계] exec.yaml, interview.yaml, 초기 bundle file 생성

  loop CLI 내부 진행이 root boundary에 도달할 때까지
    Co->>Co: [기계] interview, status, tasks 읽기
    alt 사용자 답변이 필요함
      Co-->>Root: [기계] root_action=ask_user
      Root->>User: [추론기계] root_action.question 전달
      User-->>Root: [유저] 답변
      Root->>Co: [추론기계] co.py flow respond --stdin
      Co->>Co: [기계] 답변 기록과 pending question 해제
    else 내부 진행 가능
      Co->>Agent: [기계] ask-next or ambiguity scorer
      Agent-->>Co: [추론형식] schema-bound JSON
      Co->>Co: [기계] fact 기록, ambiguity 계산, readiness streak 처리
    end
  end

  Co->>Agent: [기계] closure_auditor
  Agent-->>Co: [추론형식] pass or ask_user JSON
  alt closure audit 질문 필요
    Co-->>Root: [기계] root_action=ask_user
  else closure audit 통과
    Co->>Agent: [기계] seed_architect
    Agent-->>Co: [추론형식] plan_seed.yaml JSON
    Co->>Co: [기계] plan_seed.yaml 작성과 interview close
  end

  Co->>Agent: [기계] bundle_author
  Agent-->>Co: [추론형식] tasks.yaml JSON
  Co->>Co: [기계] task bundle 작성과 검증
  Co-->>Root: [기계] root_action=present_plan_seed

  Root->>User: [추론기계] root_action.plan_seed 표시
  User-->>Root: [유저] 승인 또는 feedback
  Root->>Co: [추론기계] co.py flow respond --stdin
  Co->>Agent: [기계] 필요한 경우 seed feedback 분류
  Agent-->>Co: [추론형식] approval, wording_change, or meaning_change JSON
  alt approval
    Co->>Co: [기계] 승인, execution 준비, task claim
    Co-->>Root: [기계] root_action=execute_task
  else wording change
    Co->>Agent: [기계] seed_reviser
    Co->>Agent: [기계] bundle_author
    Co->>Co: [기계] validation 재실행
    Co-->>Root: [기계] root_action=present_plan_seed
  else meaning change
    Co->>Co: [기계] track 재개방, feedback 답변 기록, 재계산
    Co-->>Root: [기계] root_action=ask_user or present_plan_seed
  end
```

### Flowchart

```mermaid
flowchart TD
  Start(["[유저] planning 요청"])
  Init["[추론기계] co.py flow init"]
  Iterate["[기계] Socratic interview와 ambiguity gate 진행"]
  Boundary{"[기계] root boundary?"}
  Question["[추론기계] 질문 전달"]
  Answer["[유저] 답변 또는 수정"]
  Audit["[추론형식] closure audit"]
  Seed["[추론형식] plan seed 생성"]
  Tasks["[추론형식] task bundle 생성"]
  SeedReady{"[기계] plan seed 표시 가능?"}
  Present["[추론기계] plan seed 표시"]
  Feedback{"[유저] 승인?"}
  Meaning["[유저] 의미 변경 또는 누락 요구"]
  Wording["[유저] 문구 수정"]
  Revise["[추론형식] plan seed 수정"]
  Finalize["[기계] bundle 승인과 execution 준비"]
  Handoff(["[추론기계] execution 흐름으로 이동"])

  Start --> Init
  Init --> Iterate
  Iterate --> Boundary
  Boundary -->|ask_user| Question
  Question --> Answer
  Answer --> Iterate
  Boundary -->|seed ready| Audit
  Audit --> Seed
  Seed --> Tasks
  Tasks --> SeedReady
  SeedReady -->|yes| Present
  Present --> Feedback
  Feedback -->|no, meaning change| Meaning
  Meaning --> Iterate
  Feedback -->|no, wording only| Wording
  Wording --> Revise
  Revise --> Tasks
  Feedback -->|yes| Finalize
  Finalize --> Handoff

  linkStyle default stroke:#616161,stroke-width:1.5px
```

## Coexec

### Sequence Diagram

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

### Flowchart

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
