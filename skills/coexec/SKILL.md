---
name: coexec
description: active plan bundle의 current task를 `co.py flow`로 실행하는 root-agent용 executor 스킬.
---

# Coexec

너는 이 스킬을 실행하는 root agent다.

목표는 active plan bundle에서 CLI가 지정한 current task만 구현하고, mechanical 검증과 semantic self-review를 기록한 뒤 `co.py flow task-done`으로 task 완료를 선언하는 것이다.

## 핵심 계약

- 실행 시작과 재개는 `co.py flow next`로 한다.
- 실행 루프용 `co.py flow` 응답은 YAML이며 `contract_version`, `mode`, `phase`, `root_action`을 확인한다.
- `co.py flow status`는 read-only 진단 YAML이며 root action source가 아니다.
- Root agent는 `root_action.task`에 있는 current task만 구현한다.
- `root_action.plan_seed`는 승인된 전역 계약이다. Current task와 충돌하거나 scope, non-goals, constraints, success criteria, verification expectations, execution boundaries를 바꾸는 선택이 필요하면 halt한다.
- Mechanical 검증은 root agent가 실제 shell에서 실행하고 `co.py flow evidence --kind mechanical`로 기록한다.
- Semantic 검증은 root agent가 직접 self-review로 수행하고 `co.py flow evidence --kind semantic`으로 기록한다.
- `co.py flow evidence`는 검증 기록만 남기며 task 상태를 `Done`으로 바꾸지 않는다.
- 모든 required mechanical/semantic 기록이 pass 상태일 때만 `co.py flow task-done --stdin`으로 완료 요약을 보내 task 완료를 선언한다.
- 실패 후 수정이 필요하면 현재 task 범위 안에서만 고친다.
- Task 선택, task 완료, 다음 task, halt, finish는 `co.py flow`가 `root_action`으로 알려준다.
- Bundle YAML file은 CLI가 쓰는 실행 상태다. Root agent가 직접 수정하지 않는다.
- `co.py` 커맨드가 길게 실행되는 동안에는 새 root boundary, 실패, 사용자 입력 필요 상태가 나오기 전까지 반복 진행 보고 없이 기다린다.

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
    next_required_action: Continue T01 until mechanical checks, semantic self-review, and task-done completion gate pass.
    missing_verification:
      - mechanical:focused
      - semantic:acceptance
  task_view:
    files:
      primary:
        - path/to/file
      generated_incidental: []
    verification:
      mechanical:
        - id: focused
          command: test command
          success_signal: expected signal
      semantic:
        - id: acceptance
          lens: Acceptance criteria
          review_prompt: Check the implementation against this task and the approved plan seed.
          pass_signal: No acceptance criterion is missing.
    acceptance_criteria:
      - expected behavior
  evidence_state:
    required:
      mechanical:
        - focused
      semantic:
        - acceptance
    recorded: []
    missing:
      - mechanical:focused
      - semantic:acceptance
  task_done_command: co.py flow task-done --stdin
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
CLI가 task 선택, repair boundary, verification state, halt, finish 판단을 끝낸 뒤 이 객체만 root agent에게 공개한다.

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
`files`는 주요 파일 범위, `verification.mechanical`은 실행할 local command checks, `verification.semantic`은 root agent가 직접 수행할 self-review checks, `acceptance_criteria`는 완료 기준이다.

### `root_action.evidence_state`

현재 task의 required mechanical/semantic checks와 이미 기록된 verification records를 담는다.
누락된 check를 모두 pass로 기록한 뒤 `co.py flow task-done`을 실행한다.

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

무엇인지:
CLI가 current task를 claim했고, root agent가 구현과 검증을 수행해야 하는 상태다.

해야 할 일:
`root_action.task`와 `root_action.task_view` 범위 안에서만 구현한다.
`root_action.plan_seed`의 goal, constraints, non-goals, success criteria, verification expectations, execution boundaries와 충돌하지 않는지 확인한다.
구현 후 `root_action.task_view.verification.mechanical[*]`의 command를 실제 shell에서 실행하고 결과를 `co.py flow evidence --kind mechanical`로 기록한다.
각 evidence 기록 직후 반환된 `root_action.type`을 확인하고, `repair_task`나 `report_error`가 반환되면 다음 check로 진행하지 않는다.
Mechanical 기록이 계속 실행 가능한 상태를 반환할 때만 `root_action.task_view.verification.semantic[*]`의 lens와 review_prompt에 따라 root agent가 직접 self-review를 수행하고 `co.py flow evidence --kind semantic`으로 기록한다.
모든 required checks가 pass로 기록되면 `co.py flow task-done --stdin`에 완료 요약을 보내 task 완료를 선언한다.
Task 범위를 바꾸거나 plan seed를 바꿔야 하면 구현하지 말고 `co.py flow halt`로 멈춘다.

### `repair_task`

무엇인지:
현재 task의 mechanical 또는 semantic 검증 실패가 기록되어 같은 task 안에서 고쳐야 하는 상태다.

해야 할 일:
`root_action.latest_failed_evidence`와 recorded artifact를 기준으로 실패 원인을 확인한다.
현재 task 범위 안에서만 수정한다.
실패한 mechanical command나 semantic self-review를 다시 수행하고 `co.py flow evidence`로 새 기록을 남긴다.
각 evidence 기록 직후 반환된 `root_action.type`을 확인하고, 같은 실패가 반복되면 계속 진행하지 말고 원인을 다시 고친다.
모든 required checks가 pass가 되면 `co.py flow task-done --stdin`을 실행한다.

### `report_halt`

무엇인지:
CLI가 더 진행할 수 없는 중단 상태를 기록한 것이다.

해야 할 일:
`root_action.halt` 내용을 사용자에게 보고하고 멈춘다.
Root agent가 우회 경로나 새 task 결정을 만들지 않는다.

### `report_complete`

무엇인지:
CLI가 모든 task와 finish gate를 완료 상태로 판정한 것이다.

해야 할 일:
최종 완료를 보고한다.
최종 보고 첫 줄은 정확히 `최종 완료`로 쓴다.

### `report_error`

무엇인지:
CLI command 처리 중 복구되지 않은 오류가 발생한 것이다.

해야 할 일:
`root_action.message`를 사용자에게 보고하고 멈춘다.
Root agent가 bundle file을 직접 고치거나 error를 자체 복구하지 않는다.

## Execution Workflow

| 주체 | 역할 |
|---|---|
| User | Halt 또는 completion report를 받는다. |
| Root agent | CLI가 반환한 current task만 구현하고 mechanical/semantic verification을 수행한다. |
| `co.py` CLI | Current task, verification records, task-done gate, halt, completion을 관리한다. |

기본 흐름은 아래와 같다.

```text
co.py flow next
execute_task 또는 repair_task 수행
mechanical verification 실행과 기록
반환된 root_action 처리
semantic self-review 수행과 기록
반환된 root_action 처리
co.py flow task-done --stdin
다음 root_action 처리
반복
```

## Mechanical Evidence 기록

Mechanical verification은 `root_action.task_view.verification.mechanical[*]`에 있는 check를 기준으로 실행한다.
`--check`에는 실행한 mechanical check의 `id`를 넣는다.
`--command`에는 실제 실행한 shell command를 그대로 넣는다.
`--success true`는 exit code와 output이 해당 check의 `success_signal`을 만족할 때만 쓴다.
Non-zero exit code는 successful mechanical evidence로 기록할 수 없다.

```bash
set +e
command='<mechanical command from root_action.task_view.verification.mechanical[*].command>'
output="$(sh -lc "$command" 2>&1)"
code=$?
printf '%s\n' "$output" | ~/.codex/skills/coplan/scripts/co.py flow evidence \
  --kind mechanical \
  --check <mechanical-check-id> \
  --command "$command" \
  --exit-code "$code" \
  --success true|false \
  --stdin
```

이 명령이 `root_action.type: repair_task` 또는 `report_error`를 반환하면 semantic review나 `task-done`으로 진행하지 않는다.

## Semantic Evidence 기록

Semantic verification은 root agent가 직접 수행하는 self-review다.
각 review는 current task, `plan_seed`, changed files, recorded mechanical output, acceptance criteria를 기준으로 판단한다.
`pass`는 review body에 pass 근거가 있고 해당 `pass_signal`을 만족할 때만 쓴다.

```bash
printf '%s\n' "<semantic self-review body>" | ~/.codex/skills/coplan/scripts/co.py flow evidence \
  --kind semantic \
  --check <semantic-check-id> \
  --status pass|fail \
  --stdin
```

이 명령이 `root_action.type: repair_task` 또는 `report_error`를 반환하면 `task-done`으로 진행하지 않는다.

## Task 완료

Evidence 기록은 task를 자동 완료하지 않는다.
모든 required mechanical/semantic checks가 pass로 기록된 뒤 완료 요약을 보낸다.

```bash
printf '%s\n' "<task completion summary>" | ~/.codex/skills/coplan/scripts/co.py flow task-done --stdin
```

`task-done`이 missing verification을 반환하면 해당 missing check를 수행하고 다시 `task-done`을 실행한다.

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
- Semantic review를 통과 처리하기 위해 실패한 mechanical result나 미충족 acceptance criterion을 무시하지 않는다.

## 보고 기준

- `report_complete`이면 최종 보고 첫 줄은 정확히 `최종 완료`로 쓴다.
- 중간에 멈추면 현재 `root_action.type` 또는 `root_action.halt`를 보고한다.
- 실행한 mechanical command와 semantic self-review pass/fail을 짧게 보고한다.
