---
name: coplan
description: 사용자 요청을 `co.py flow`로 실행 가능한 plan bundle로 정리하는 root-agent용 planner 스킬.
---

# Coplan

너는 이 스킬을 실행하는 root agent다.

목표는 사용자 요청을 `co.py flow`에 전달하고, CLI가 돌려주는 `root_action`을 수행해서 실행 가능한 `.agents/plan/{plan-id}/` plan bundle을 만드는 것이다. 이 스킬을 사용하는 동안 실제 source code 구현은 하지 않는다.

## 핵심 계약

- `co.py flow`가 다음 행동을 `root_action`으로 반환한다.
- 모든 `co.py flow` 응답은 YAML이며 `contract_version`, `mode`, `phase`, `root_action`을 확인한다.
- Root agent는 반환된 `root_action` 하나만 수행한다.
- 사용자에게 물어야 할 내용은 `root_action.question` 그대로 묻는다.
- 사용자에게 보여줄 계획 계약은 `root_action.plan_seed` 그대로 보여준다.
- 사용자 요청, 답변, approval, feedback은 요약·번역·정리하지 않는다.
- 사용자 답변, approval, feedback은 `co.py flow respond --stdin`으로 전달한다.
- Bundle file은 CLI가 쓰는 실행 상태다. Root agent가 직접 수정하지 않는다.
- `root_action.type`이 executor action이면 planning이 끝난 것이므로 `coexec`를 실행한다.

## Flow Stdout

`co.py flow`는 root agent가 처리해야 할 정보만 YAML로 반환한다.
stdout 전체가 다음 행동을 정하는 계약이므로, root agent는 이 YAML을 읽고 `root_action` 하나만 수행한다.

```yaml
contract_version: '1'
mode: planner
phase: planning
root_action:
  type: continue_flow
  message: Run `co.py flow next` to continue planning.
  next_command: co.py flow next
```

## 공통 YAML 필드

### `contract_version`

`co.py flow` stdout 계약 버전이다.
Root agent는 값을 해석해 새 규칙을 만들지 않고, 현재 문서의 계약대로 `root_action`을 처리한다.

### `mode`

현재 root boundary의 큰 모드다.
`planner`는 coplan이 계속 처리한다.
`executor`는 planning이 끝났거나 execution 경계에 도달했다는 뜻이므로 `coexec`를 실행한다.
`halted`, `complete`, `error`는 사용자에게 보고하고 멈추는 모드다.

### `phase`

Active plan의 저장된 상태다.
Root agent는 `phase`로 다음 행동을 추론하지 않고, 항상 `root_action.type`을 따른다.

### `root_action`

Root agent가 지금 수행해야 하는 단 하나의 행동이다.
CLI가 내부 상태 전이, interview 판단, review, task 선택을 끝낸 뒤 이 객체만 root agent에게 공개한다.

### `root_action.type`

`root_action`의 종류다.
이 값이 `continue_flow`, `ask_user`, `present_plan_seed`, `execute_task`, `repair_task`, `report_halt`, `report_complete`, `report_error` 중 무엇인지 확인하고, 아래 같은 이름의 섹션만 따른다.

### `root_action.*_command`

`next_command`, `response_command` 같은 command field는 root agent가 실행할 CLI 명령이다.
명령 문자열을 재구성하지 말고 그대로 실행한다.

### `root_action`의 나머지 payload

`question`, `plan_seed`, `task`, `halt`, `message` 같은 field는 해당 action을 수행하는 데 필요한 입력이다.
Root agent는 payload를 해석해서 새 결정을 만들지 않고, 사용자 표시나 다음 skill 실행에 필요한 만큼만 사용한다.

## 시작

새 plan은 아래 명령으로 시작한다.

```bash
printf '%s\n' "<사용자 요청 원문>" | ~/.codex/skills/coplan/scripts/co.py flow init --plan-id <stable-kebab-id> --title "<title>" --stdin
```

그다음 아래 명령으로 다음 경계를 받는다.

```bash
~/.codex/skills/coplan/scripts/co.py flow next
```

위 명령은 내부 CLI의 처리 과정으로 인해 10분 이상 충분히 길어질 수 있으므로 커맨드를 임의로 중지하거나 재시도하지 않고 기다린다.

## Root Action 처리

### 공통 원칙

`root_action.type`을 먼저 확인하고, 해당 action 하나만 수행한다.
`root_action`에 없는 다음 단계, 질문, 판단, 명령을 만들지 않는다.
`co.py` CLI가 내부 Codex CLI subagent를 실행하더라도 Root agent는 subagent를 직접 호출하거나 결과를 해석하지 않는다.

### `continue_flow`

샘플 YAML:

```yaml
contract_version: '1'
mode: planner
phase: planning
root_action:
  type: continue_flow
  message: Run `co.py flow next` to continue planning.
  next_command: co.py flow next
```

무엇인지:
CLI가 사용자에게 보여줄 질문이나 plan seed 없이 내부 flow를 더 진행할 수 있다는 뜻이다.

해야 할 일:
`root_action.next_command`를 그대로 실행한다.
보통 `co.py flow next`이며, 명령이 오래 걸려도 임의로 중지하거나 같은 명령을 중복 실행하지 않는다.

### `ask_user`

샘플 YAML:

```yaml
contract_version: '1'
mode: planner
phase: planning
root_action:
  type: ask_user
  question: 'Change: 어떤 동작을 바꾸려는지, 보존해야 할 공개 동작은 무엇인가요?'
  response_command: co.py flow respond --stdin
```

무엇인지:
CLI가 다음 계획 결정을 위해 사용자 판단이 필요하다고 판정한 상태다.

해야 할 일:
`root_action.question`만 사용자에게 그대로 묻는다.
질문에 설명, 예시, 선택지, 요약, 번역을 덧붙이지 않는다.
사용자 답변은 요약·번역·정리하지 않고 `co.py flow respond --stdin`으로 전달한다.

### `present_plan_seed`

샘플 YAML:

```yaml
contract_version: '1'
mode: planner
phase: seed_review
root_action:
  type: present_plan_seed
  plan_seed:
    status: ready
    seed:
      title: Example plan
      goal: User-reviewed goal
      constraints: []
      non_goals: []
      success_criteria: []
      verification_expectations: []
      execution_boundaries: []
  response_command: co.py flow respond --stdin
```

무엇인지:
CLI가 interview, ambiguity scoring, closure audit, bundle review를 통과해 사용자 검토용 계획 계약을 만든 상태다.

해야 할 일:
`root_action.plan_seed`를 사용자에게 그대로 보여준다.
Root agent가 plan seed 내용을 다시 요약하거나 approval 여부를 대신 판단하지 않는다.
사용자의 approval 또는 feedback은 요약·번역·정리하지 않고 `co.py flow respond --stdin`으로 전달한다.

### `execute_task`

샘플 YAML:

```yaml
contract_version: '1'
mode: executor
phase: executing
root_action:
  type: execute_task
  active_plan:
    id: example-plan
  task:
    id: T01
    title: Implement approved change
  plan_seed:
    seed:
      goal: User-approved goal
  status:
    id: T01
    title: Implement approved change
    status: Doing
    next_required_action: Continue T01 until required evidence is recorded and completion gates pass.
  task_view:
    files:
      primary: []
      generated_incidental: []
    verification:
      evidence_required: true
      steps: []
    acceptance_criteria: []
  evidence_state:
    required: []
    recorded: []
  notes: []
```

무엇인지:
Planning이 끝났고 executor가 수행할 current task가 지정된 상태다.

해야 할 일:
Planning이 끝난 상태다.
이 스킬에서 source code를 구현하지 않고 `coexec`를 실행한다.

### `repair_task`

샘플 YAML:

```yaml
contract_version: '1'
mode: executor
phase: executing
root_action:
  type: repair_task
  active_plan:
    id: example-plan
  task:
    id: T01
    title: Implement approved change
  plan_seed:
    seed:
      goal: User-approved goal
  status:
    id: T01
    title: Implement approved change
    status: Doing
    next_required_action: Continue T01 until required evidence is recorded and completion gates pass.
  task_view:
    files:
      primary: []
      generated_incidental: []
    verification:
      evidence_required: true
      steps: []
    acceptance_criteria: []
  evidence_state:
    required: []
    recorded: []
  notes: []
  latest_failed_evidence:
    step_id: verify
    success: false
```

무엇인지:
Execution 중 검증 실패나 repair boundary가 발생해 executor가 같은 task 안에서 고쳐야 하는 상태다.

해야 할 일:
Execution 경계에 도달한 상태다.
이 스킬에서 repair를 수행하지 않고 `coexec`를 실행한다.

### `report_halt`

샘플 YAML:

```yaml
contract_version: '1'
mode: halted
phase: halted
root_action:
  type: report_halt
  halt:
    kind: user_decision
    reason: User decision is required before continuing.
```

무엇인지:
CLI가 더 진행할 수 없는 중단 상태를 기록한 것이다.

해야 할 일:
`root_action.halt` 내용을 사용자에게 보고하고 멈춘다.
Root agent가 우회 경로나 새 계획을 만들지 않는다.

### `report_complete`

샘플 YAML:

```yaml
contract_version: '1'
mode: complete
phase: complete
root_action:
  type: report_complete
  active_plan:
    id: example-plan
  progress:
    done:
      - T01
    doing: []
    todo: []
```

무엇인지:
CLI가 모든 task와 finish gate를 완료 상태로 판정한 것이다.

해야 할 일:
완료 상태를 사용자에게 보고한다.

### `report_error`

샘플 YAML:

```yaml
contract_version: '1'
mode: error
phase: planning
root_action:
  type: report_error
  message: CLI가 보고한 에러 내용
```

무엇인지:
CLI command 처리 중 복구되지 않은 오류가 발생한 것이다.

해야 할 일:
`root_action.message`를 사용자에게 보고하고 멈춘다.
Root agent가 bundle file을 직접 고치거나 error를 자체 복구하지 않는다.

## Planning Workflow

| 주체          | 역할                                                                   |
|-------------|----------------------------------------------------------------------|
| User        | 요청, 답변, plan seed approval 또는 feedback을 제공한다.                        |
| Root agent  | `co.py flow`를 실행하고, 질문과 plan seed를 사용자에게 전달하고, 사용자 응답을 CLI로 되돌려 보낸다. |
| `co.py` CLI | 다음 root boundary를 `root_action`으로 반환하고 bundle state를 기록한다.           |

기본 흐름은 아래와 같다.

```text
co.py flow init
co.py flow next
root_action 처리
co.py flow respond --stdin 또는 co.py flow next
반복
```

Planning이 끝나면 `root_action.type: execute_task`가 반환되고, root agent는 `coexec`를 실행한다.
인터뷰가 충분해 보여도 `co.py flow`가 closure audit 질문을 `ask_user`로 반환할 수 있다. 이 경우에도 다른 질문과 동일하게 그대로 묻고 답변을
전달한다.

## 명령 제한

Planning 중 사용하는 flow command는 아래뿐이다.

```bash
printf '%s\n' "<사용자 요청 원문>" | ~/.codex/skills/coplan/scripts/co.py flow init --plan-id <id> --title "<title>" --stdin [--replace]
~/.codex/skills/coplan/scripts/co.py flow next
~/.codex/skills/coplan/scripts/co.py flow respond --stdin
~/.codex/skills/coplan/scripts/co.py flow status
```

필요하면 read-only command는 사용할 수 있다.

```bash
~/.codex/skills/coplan/scripts/co.py current
~/.codex/skills/coplan/scripts/co.py show --file tasks|plan-seed|interview|status|notes|evidence
```

## 금지 사항

- `plan_seed.yaml`, `tasks.yaml`, `interview.yaml`, `status.yaml`, `notes.yaml`, `evidence.yaml`을 직접
  수정하지 않는다.
- `root_action`에 없는 다음 단계를 임의로 만들지 않는다.
- Planning 중 source code를 구현하지 않는다.
- 명시적으로 요청받기 전에는 commit, branch, push, PR을 만들지 않는다.

## 보고 기준

- 현재 plan이 생겼으면 `co.py current` 기준으로 active plan을 보고한다.
- 사용자 입력이 필요한 상태면 질문 또는 plan seed만 보여준다.
- 중간에 멈추면 `report_error` 또는 `report_halt` 내용을 그대로 설명한다.
