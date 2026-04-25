---
name: coexec
description: active plan bundle의 current task를 `co.py flow`로 실행하는 root-agent용 executor 스킬.
---

# Coexec

너는 이 스킬을 실행하는 root agent다.

목표는 active plan bundle에서 CLI가 지정한 current task만 구현하고, 검증 결과를 `co.py flow`에 기록해서 다음 root boundary를 받는 것이다.

## 핵심 계약

- 실행 시작과 재개는 `co.py flow next`로 한다.
- 모든 `co.py flow` 응답은 YAML이며 `contract_version`, `mode`, `phase`, `root_action`을 확인한다.
- Root agent는 `root_action.task`에 있는 current task만 구현한다.
- `root_action.plan_seed`는 승인된 전역 계약이다. Current task와 충돌하지 않는지 확인하고, scope, non-goals, constraints, success criteria, verification expectations, execution boundaries를 바꾸는 선택이 필요하면 halt한다.
- 검증 명령은 root agent가 실제 shell에서 실행한다.
- 검증 output, exit code, success 여부는 `co.py flow evidence`로 기록한다.
- 실패 후 수정이 필요하면 현재 task 범위 안에서만 고친다.
- Task 선택, task 완료, 다음 task, halt, finish는 `co.py flow`가 `root_action`으로 알려준다.
- Bundle YAML file은 CLI가 쓰는 실행 상태다. Root agent가 직접 수정하지 않는다.

## Flow Stdout

`co.py flow`는 root agent가 처리해야 할 정보만 YAML로 반환한다.

```yaml
contract_version: '1'
mode: planner|executor|halted|complete|error
phase: executing
root_action:
  type: continue_flow|execute_task|repair_task|report_halt|report_complete|report_error
```

`phase`는 active plan 상태다.
에러도 `mode: error`와 `root_action.type: report_error`로 표현된다.
항상 `root_action.type`에 맞는 행동 하나만 수행한다.

Executor에서 주로 받는 `root_action` 모양은 아래와 같다.

```yaml
root_action:
  type: execute_task|repair_task
  active_plan:
    id: plan-id
  task:
    id: task-id
    title: task title
  plan_seed:
    seed:
      goal: approved goal
      constraints: []
      non_goals: []
      success_criteria: []
      verification_expectations: []
      execution_boundaries: []
  status:
    id: task-id
    status: Doing
  task_view:
    files:
      primary:
        - path/to/file
      generated_incidental: []
    verification:
      evidence_required: true
      steps:
        - id: verification-step-id
          command: verification command
          success_signal: expected signal
    acceptance_criteria:
      - expected behavior
  evidence_state:
    required:
      - evidence artifact path
    recorded:
      - evidence artifact path
  notes: []
  latest_failed_evidence: {}
```

`latest_failed_evidence`는 실패 evidence가 있을 때만 온다.

```yaml
root_action:
  type: report_error
  message: CLI가 보고한 에러 내용
```

## 시작

아래 명령으로 현재 execution boundary를 받는다.

```bash
~/.codex/skills/coplan/scripts/co.py flow next
```

## Root Action 처리

| `root_action.type` | 수행 |
|---|---|
| `continue_flow` | `root_action.next_command`를 실행한다. 보통 `co.py flow next`다. |
| `execute_task` | `root_action.task` 범위 안에서 구현하고 지정된 verification을 실행한다. |
| `repair_task` | 현재 task 범위 안에서 실패 원인을 고치고 verification을 다시 실행한다. |
| `report_halt` | `root_action.halt`를 사용자에게 보고하고 멈춘다. |
| `report_complete` | 최종 완료를 보고한다. |
| `report_error` | `root_action.message`를 사용자에게 보고하고 멈춘다. |

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

## Repair와 Halt

Task metadata가 현재 구현 현실과 맞지 않지만 사용자-facing contract는 바뀌지 않는 경우에만 repair를 사용한다.

```bash
~/.codex/skills/coplan/scripts/co.py flow repair \
  --field <files|implementation_notes|verification path> \
  --reason "<reason>" \
  --set|--add|--remove <yaml-value>
```

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
