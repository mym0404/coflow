# Coplan 흐름도

이 문서는 `coplan`이 사용자 요청을 실행 가능한 plan bundle로 바꾸는 흐름을 보여주는 사용자용 문서다.
그래프의 초점은 user, root agent, `co.py flow`, Codex CLI agent 사이에서 제어가 이동하는 방식이다.

## Sequence Diagram

```mermaid
sequenceDiagram
  participant User as user
  participant Root as root agent
  participant Co as co.py flow
  participant Agent as Codex CLI agent

  User->>Root: [유저] planning 요청
  Root->>Co: [추론기계] co.py flow init --plan-id ... --title ... --stdin
  Co->>Co: [기계] exec.yaml, interview.yaml, 초기 bundle file 생성
  Co-->>Root: [기계] root_action=continue_flow

  loop root boundary에 도달할 때까지
    Root->>Co: [추론기계] co.py flow next or co.py flow respond --stdin
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

  loop bundle review가 통과할 때까지
    par contract review
      Co->>Agent: [기계] contract_reviewer
      Agent-->>Co: [추론형식] PASS or FAIL JSON
    and verification review
      Co->>Agent: [기계] verification_reviewer
      Agent-->>Co: [추론형식] PASS or FAIL JSON
    end
    alt reviewer 실패
      Co->>Agent: [기계] bundle_author with findings
      Agent-->>Co: [추론형식] revised tasks.yaml JSON
      Co->>Co: [기계] task bundle 재작성과 검증
    else reviewer 통과
      Co-->>Root: [기계] root_action=present_plan_seed
    end
  end

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
    Co->>Co: [기계] validation과 parallel review 재실행
    Co-->>Root: [기계] root_action=present_plan_seed
  else meaning change
    Co->>Co: [기계] track 재개방, feedback 답변 기록, 재계산
    Co-->>Root: [기계] root_action=ask_user or present_plan_seed
  end
```

## Flowchart

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
  Review["[기계] bundle review gate"]
  SeedReady{"[기계] plan seed 표시 가능?"}
  Repair["[추론형식] finding 반영"]
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
  Tasks --> Review
  Review --> SeedReady
  SeedReady -->|no| Repair
  Repair --> Tasks
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
  linkStyle 0,4,14,15,16,17,18,19 stroke:#2e7d32,stroke-width:2px
  linkStyle 1,3,12,13,20 stroke:#1565c0,stroke-width:2px
  linkStyle 2,5,6,7,8,11 stroke:#f9a825,stroke-width:2px
```

## Label Meaning

- `[기계]`: file read/write, schema validation, state transition, subprocess launch, stdout emission처럼 코드로 실행되는 단계.
- `[추론기계]`: root agent가 `co.py flow`를 호출하거나 `root_action`의 사용자 표시 내용을 전달하는 단계.
- `[유저]`: 사용자가 작성한 요청, 답변, feedback, approval.
- `[추론형식]`: JSON schema 같은 정해진 출력 형식 안에서 이뤄지는 AI 판단.
- Flowchart edge 색상은 같은 역할을 따른다. green은 `[유저]`, blue는 `[추론기계]`, gray는 `[기계]`, yellow는 `[추론형식]`이다.
