# Coplan 흐름도

이 문서는 `coplan`이 사용자 요청을 실행 가능한 plan bundle로 바꾸는 흐름을 보여주는 사용자용 문서다.
그래프의 초점은 user, root agent, `co flow`, Codex CLI agent 사이에서 제어가 이동하는 방식이다.

## Sequence Diagram

```mermaid
sequenceDiagram
  participant User as user
  participant Root as root agent
  participant Co as co flow
  participant Agent as Codex CLI agent

  User->>Root: [유저] planning 요청
  Root->>Co: [추론기계] co flow init --plan-id ... --title ...
  Co->>Co: [기계] exec.yaml과 초기 bundle file 생성
  Co-->>Root: [기계] root_action=continue_flow

  loop root boundary에 도달할 때까지
    Root->>Co: [추론기계] co flow next or co flow respond --stdin
    Co->>Co: [기계] interview, status, context 읽기
    alt 사용자 답변이 필요함
      Co-->>Root: [기계] root_action=ask_user
      Root->>User: [추론기계] root_action.question 전달
      User-->>Root: [유저] 답변
      Root->>Co: [추론기계] co flow respond --stdin
      Co->>Co: [기계] 답변 기록과 pending question 해제
    else 내부 진행 가능
      Co->>Agent: [기계] ask-next or ambiguity scorer
      Agent-->>Co: [추론형식] schema-bound JSON
      Co->>Co: [기계] fact 기록, ambiguity 계산, interview gate 처리
    end
  end

  Co->>Agent: [기계] bundle_author
  Agent-->>Co: [추론형식] draft.md, plan.yaml, tasks.yaml JSON
  Co->>Co: [기계] bundle file 작성과 검증

  loop pre-draft review가 통과할 때까지
    par contract review
      Co->>Agent: [기계] contract_reviewer
      Agent-->>Co: [추론형식] PASS or FAIL JSON
    and verification review
      Co->>Agent: [기계] verification_reviewer
      Agent-->>Co: [추론형식] PASS or FAIL JSON
    end
    alt reviewer 실패
      Co->>Agent: [기계] bundle_author with findings
      Agent-->>Co: [추론형식] revised bundle JSON
      Co->>Co: [기계] bundle file 재작성과 검증
    else reviewer 통과
      Co-->>Root: [기계] root_action=present_draft
    end
  end

  Root->>User: [추론기계] root_action.draft 표시
  User-->>Root: [유저] 승인 또는 feedback
  Root->>Co: [추론기계] co flow respond --stdin
  Co->>Agent: [기계] 필요한 경우 draft feedback 분류
  Agent-->>Co: [추론형식] approval, wording_change, or meaning_change JSON
  alt approval
    Co->>Co: [기계] 승인, finalize, execution 준비, task claim
    Co-->>Root: [기계] root_action=execute_task
  else wording change
    Co->>Agent: [기계] bundle_author with wording feedback
    Co->>Co: [기계] validation과 parallel review 재실행
    Co-->>Root: [기계] root_action=present_draft
  else meaning change
    Co->>Co: [기계] track 재개방, feedback 답변 기록, 재계산
    Co-->>Root: [기계] root_action=ask_user or present_draft
  end
```

## Flowchart

```mermaid
flowchart TD
  Start(["[유저] planning 요청"])
  Init["[추론기계] co flow init"]
  Iterate["[기계] interview 상태 진행"]
  Boundary{"[기계] root boundary?"}
  Question["[추론기계] 질문 전달"]
  Answer["[유저] 답변 또는 수정"]
  Draft["[추론형식] plan draft 생성"]
  Review["[기계] 구조 검증과 review gate"]
  DraftReady{"[기계] draft 표시 가능?"}
  Repair["[추론형식] finding 반영"]
  Present["[추론기계] draft 표시"]
  Feedback{"[유저] 승인?"}
  Meaning["[유저] 의미 변경 또는 누락 요구"]
  Wording["[유저] 문구 수정"]
  Finalize["[기계] bundle 승인과 execution 준비"]
  Handoff(["[추론기계] execution 흐름으로 이동"])

  Start --> Init
  Init --> Iterate
  Iterate --> Boundary
  Boundary -->|ask_user| Question
  Question --> Answer
  Answer --> Iterate
  Boundary -->|draft possible| Draft
  Draft --> Review
  Review --> DraftReady
  DraftReady -->|no| Repair
  Repair --> Review
  DraftReady -->|yes| Present
  Present --> Feedback
  Feedback -->|no, meaning change| Meaning
  Meaning --> Iterate
  Feedback -->|no, wording only| Wording
  Wording --> Draft
  Feedback -->|yes| Finalize
  Finalize --> Handoff

  linkStyle default stroke:#616161,stroke-width:1.5px
  linkStyle 0,4,12,13,14,15,16 stroke:#2e7d32,stroke-width:2px
  linkStyle 1,3,10,11,17 stroke:#1565c0,stroke-width:2px
  linkStyle 2,5,6,9 stroke:#f9a825,stroke-width:2px
```

## Label Meaning

- `[기계]`: file read/write, schema validation, state transition, subprocess launch, stdout emission처럼 코드로 실행되는 단계.
- `[추론기계]`: root agent가 `co flow`를 호출하거나 `root_action`의 사용자 표시 내용을 전달하는 단계.
- `[유저]`: 사용자가 작성한 요청, 답변, feedback, approval.
- `[추론형식]`: JSON schema 같은 정해진 출력 형식 안에서 이뤄지는 AI 판단.
- Flowchart edge 색상은 같은 역할을 따른다. green은 `[유저]`, blue는 `[추론기계]`, gray는 `[기계]`, yellow는 `[추론형식]`이다.
