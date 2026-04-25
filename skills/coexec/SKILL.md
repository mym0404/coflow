---
name: coexec
description: active plan bundle의 current task를 `co.py flow`로 실행하는 root-agent용 executor 스킬.
---

# Coexec

너는 이 스킬을 실행하는 root agent다.

목표는 active plan bundle에서 CLI가 지정한 current task만 구현하고, 검증 결과를 `co.py flow`에 기록해서 다음 root boundary를 받는 것이다.

## 핵심 계약

- 실행 시작과 재개는 `co.py flow next`로 한다.
- 실행 루프용 `co.py flow` 응답은 YAML이며 `contract_version`, `mode`, `phase`, `root_action`을 확인한다.
- `co.py flow status`는 read-only 진단 YAML이며 root action source가 아니다.
- Root agent는 `root_action.task`에 있는 current task만 구현한다.
- `root_action.plan_seed`는 승인된 전역 계약이다. Current task와 충돌하지 않는지 확인하고, scope, non-goals, constraints, success criteria, verification expectations, execution boundaries를 바꾸는 선택이 필요하면 halt한다.
- 검증 명령은 root agent가 실제 shell에서 실행한다.
- 검증 output, exit code, success 여부는 `co.py flow evidence`로 기록한다.
- 실패 후 수정이 필요하면 현재 task 범위 안에서만 고친다.
- Task 선택, task 완료, 다음 task, halt, finish는 `co.py flow`가 `root_action`으로 알려준다.
- Bundle YAML file은 CLI가 쓰는 실행 상태다. Root agent가 직접 수정하지 않는다.

## Flow Stdout

실행 루프용 `co.py flow`는 root agent가 처리해야 할 정보만 YAML로 반환한다.
stdout 전체가 다음 행동을 정하는 계약이므로, root agent는 이 YAML을 읽고 `root_action` 하나만 수행한다.

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
      constraints: []
      non_goals: []
      success_criteria: []
      verification_expectations: []
      execution_boundaries: []
  status:
    id: T01
    title: Implement approved change
    status: Doing
    next_required_action: Continue T01 until required evidence is recorded and completion gates pass.
  task_view:
    files:
      primary:
        - path/to/file
      generated_incidental: []
    verification:
      evidence_required: true
      steps:
        - id: verify
          command: test command
          success_signal: expected signal
    acceptance_criteria:
      - expected behavior
  evidence_state:
    required:
      - evidence/t01-verify.txt
    recorded: []
  notes: []
```

## 공통 YAML 필드

### `contract_version`

`co.py flow` stdout 계약 버전이다.
Root agent는 값을 해석해 새 규칙을 만들지 않고, 현재 문서의 계약대로 `root_action`을 처리한다.

### `mode`

현재 root boundary의 큰 모드다.
`executor`는 이 스킬이 계속 처리한다.
`halted`, `complete`, `error`는 사용자에게 보고하고 멈추는 모드다.
`planner`가 나오면 실행 경계가 아니므로 `coplan`으로 돌아가야 한다.

### `phase`

Active plan의 저장된 상태다.
Root agent는 `phase`로 다음 행동을 추론하지 않고, 항상 `root_action.type`을 따른다.

### `root_action`

Root agent가 지금 수행해야 하는 단 하나의 행동이다.
CLI가 task 선택, repair boundary, evidence state, halt, finish 판단을 끝낸 뒤 이 객체만 root agent에게 공개한다.

### `root_action.type`

`root_action`의 종류다.
이 값이 `execute_task`, `repair_task`, `report_halt`, `report_complete`, `report_error` 중 무엇인지 확인하고, 아래 같은 이름의 섹션만 따른다.

### `root_action.*_command`

command field는 root agent가 실행할 CLI 명령이다.
명령 문자열을 재구성하지 말고 그대로 실행한다.

### `root_action.plan_seed`

승인된 전역 계획 계약이다.
Root agent는 current task를 수행할 때 이 계약과 충돌하지 않는지 확인한다.
이 계약을 바꾸는 선택이 필요하면 직접 수정하지 않고 `co.py flow halt`로 멈춘다.

### `root_action.task`

현재 구현해야 하는 task의 id와 title을 담는다.
Root agent는 이 task 하나만 구현한다.

### `root_action.task_view`

현재 task 수행에 필요한 실행 표면이다.
`files`는 주요 파일 범위, `verification.steps`는 실행할 검증 명령, `acceptance_criteria`는 완료 기준이다.

### `root_action.evidence_state`

현재 task의 evidence 요구와 이미 기록된 evidence 목록이다.
필요한 검증을 실행한 뒤 `co.py flow evidence`로 결과를 기록한다.

### `root_action.latest_failed_evidence`

실패 evidence가 있을 때만 포함된다.
`repair_task`에서는 이 값을 먼저 보고 같은 task 범위 안에서 실패 원인을 고친다.

## Status Stdout

`co.py flow status`는 현재 저장 상태를 확인하는 read-only 진단 명령이다.
이 명령의 YAML은 `root_action`을 포함하지 않으며, 다음 task 수행 근거로 쓰지 않는다.

## 시작

아래 명령으로 현재 execution boundary를 받는다.

```bash
~/.codex/skills/coplan/scripts/co.py flow next
```

## Root Action 처리

### 공통 원칙

`root_action.type`을 먼저 확인하고, 해당 action 하나만 수행한다.
`root_action`에 없는 task 선택, 완료 처리, skip, reorder, finish를 만들지 않는다.
Bundle YAML file을 직접 수정하지 않는다.

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
      constraints: []
      non_goals: []
      success_criteria: []
      verification_expectations: []
      execution_boundaries: []
  status:
    id: T01
    title: Implement approved change
    status: Doing
    next_required_action: Continue T01 until required evidence is recorded and completion gates pass.
  task_view:
    files:
      primary:
        - path/to/file
      generated_incidental: []
    verification:
      evidence_required: true
      steps:
        - id: verify
          command: test command
          success_signal: expected signal
    acceptance_criteria:
      - expected behavior
  evidence_state:
    required:
      - evidence/t01-verify.txt
    recorded: []
  notes: []
```

무엇인지:
CLI가 current task를 claim했고, root agent가 구현과 검증을 수행해야 하는 상태다.

해야 할 일:
`root_action.task`와 `root_action.task_view` 범위 안에서만 구현한다.
`root_action.plan_seed`의 goal, constraints, non-goals, success criteria, verification expectations, execution boundaries와 충돌하지 않는지 확인한다.
`root_action.task_view.verification.steps[*]`의 command를 실제 shell에서 실행하고, 결과를 `co.py flow evidence`로 기록한다.
`co.py flow evidence`가 반환한 다음 `root_action`을 처리한다.
Task 범위를 바꾸거나 plan seed를 바꿔야 하면 구현하지 말고 `co.py flow halt`로 멈춘다.

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
      constraints: []
      non_goals: []
      success_criteria: []
      verification_expectations: []
      execution_boundaries: []
  status:
    id: T01
    title: Implement approved change
    status: Doing
    next_required_action: Continue T01 until required evidence is recorded and completion gates pass.
  task_view:
    files:
      primary:
        - path/to/file
      generated_incidental: []
    verification:
      evidence_required: true
      steps:
        - id: verify
          command: test command
          success_signal: expected signal
    acceptance_criteria:
      - expected behavior
  evidence_state:
    required:
      - evidence/t01-verify.txt
    recorded: []
  notes: []
  latest_failed_evidence:
    step_id: verify
    success: false
```

무엇인지:
현재 task의 검증 실패나 repair boundary가 기록되어 같은 task 안에서 고쳐야 하는 상태다.

해야 할 일:
`root_action.latest_failed_evidence`와 verification output을 기준으로 실패 원인을 확인한다.
현재 task 범위 안에서만 수정하고, 같은 verification을 다시 실행한다.
재실행 결과를 `co.py flow evidence`로 기록하고, 반환된 다음 `root_action`을 처리한다.

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
Root agent가 우회 경로나 새 task 결정을 만들지 않는다.

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
최종 완료를 보고한다.
최종 보고 첫 줄은 정확히 `최종 완료`로 쓴다.

### `report_error`

샘플 YAML:

```yaml
contract_version: '1'
mode: error
phase: executing
root_action:
  type: report_error
  message: CLI가 보고한 에러 내용
```

무엇인지:
CLI command 처리 중 복구되지 않은 오류가 발생한 것이다.

해야 할 일:
`root_action.message`를 사용자에게 보고하고 멈춘다.
Root agent가 bundle file을 직접 고치거나 error를 자체 복구하지 않는다.

## Execution Workflow

| 주체 | 역할 |
|---|---|
| User | Halt 또는 completion report를 받는다. |
| Root agent | CLI가 반환한 current task만 구현하고 verification을 실제로 실행한다. |
| `co.py` CLI | Current task, repair boundary, halt, completion을 `root_action`으로 반환하고 evidence state를 기록한다. |

기본 흐름은 아래와 같다.

```text
co.py flow next
execute_task 또는 repair_task 수행
verification 실행
co.py flow evidence
다음 root_action 처리
반복
```

## Evidence 기록

Verification은 `root_action.task_view.verification.steps[*]`에 있는 step을 기준으로 실행한다.
`--step`에는 실행한 verification item의 `id`를 넣는다.
`--command`에는 실제 실행한 shell command를 그대로 넣는다.
`--success true`는 exit code와 output이 해당 step의 `success_signal`을 만족할 때만 쓴다.

Exit code를 잃지 않도록 output과 code를 먼저 잡은 뒤 evidence로 넘긴다.

```bash
set +e
command='<verification command from root_action.task_view.verification.steps[*].command>'
output="$(sh -lc "$command" 2>&1)"
code=$?
printf '%s\n' "$output" | ~/.codex/skills/coplan/scripts/co.py flow evidence \
  --step <verification-step-id> \
  --command "$command" \
  --exit-code "$code" \
  --success true|false \
  --stdin
```

`--success false`는 실패 output을 기록하고 `repair_task` 경계로 돌아가야 한다는 뜻이다.

## Halt

사용자 결정이나 외부 환경 때문에 더 진행할 수 없으면 halt한다.

```bash
~/.codex/skills/coplan/scripts/co.py flow halt \
  --kind user_decision|external_environment \
  --reason "<reason>"
```

## 금지 사항

- Task를 직접 claim, complete, skip, reorder, finish하지 않는다.
- `plan_seed.yaml`, `tasks.yaml`, `status.yaml`, `notes.yaml`, `evidence.yaml`을 직접 수정하지 않는다.
- 현재 task 밖의 source file이나 behavior를 임의로 넓히지 않는다.
- Acceptance criteria, non-goals, dependency, task order를 바꾸지 않는다.

## 보고 기준

- `report_complete`이면 최종 보고 첫 줄은 정확히 `최종 완료`로 쓴다.
- 중간에 멈추면 현재 `root_action.type` 또는 `root_action.halt`를 보고한다.
- 실행한 검증 명령과 성공/실패 결과를 짧게 보고한다.
