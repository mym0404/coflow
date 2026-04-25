---
name: coexec
description: active plan bundle의 current task를 `co flow`로 실행하는 root-agent용 executor 스킬.
---

# Coexec

너는 이 스킬을 실행하는 root agent다.

목표는 active plan bundle에서 CLI가 지정한 current task만 구현하고, 검증 결과를 `co flow`에 기록해서 다음 root boundary를 받는 것이다.

## 핵심 계약

- 실행 시작과 재개는 `co flow next`로 한다.
- 모든 `co flow` 응답은 YAML이며 `ok`, `contract_version`, `mode`, `phase`, `root_action`을 확인한다.
- Root agent는 `root_action.task`에 있는 current task만 구현한다.
- 검증 명령은 root agent가 실제 shell에서 실행한다.
- 검증 output, exit code, success 여부는 `co flow evidence`로 기록한다.
- 실패 후 수정이 필요하면 현재 task 범위 안에서만 고친다.
- Task 선택, task 완료, 다음 task, halt, finish는 `co flow`가 `root_action`으로 알려준다.
- Bundle YAML file은 CLI가 쓰는 실행 상태다. Root agent가 직접 수정하지 않는다.

## Flow Stdout

`co flow`는 아래 핵심 필드를 포함한 YAML을 반환한다.

```yaml
ok: true
contract_version: '1'
mode: planner|executor|halted|complete|error
phase: executing
root_action:
  type: continue_flow|execute_task|repair_task|report_halt|report_complete
```

`ok: false`이면 `error`와 `root_action`을 함께 보고 다음 행동을 정한다.
`ok: true`이면 `root_action.type`에 맞는 행동 하나만 수행한다.

## 시작

아래 명령으로 현재 execution boundary를 받는다.

```bash
~/.codex/skills/coplan/scripts/co flow next
```

## Root Action 처리

| `root_action.type` | 수행 |
|---|---|
| `continue_flow` | `root_action.next_command`를 실행한다. 보통 `co flow next`다. |
| `execute_task` | `root_action.task` 범위 안에서 구현하고 지정된 verification을 실행한다. |
| `repair_task` | 현재 task 범위 안에서 실패 원인을 고치고 verification을 다시 실행한다. |
| `report_halt` | `root_action.halt`를 사용자에게 보고하고 멈춘다. |
| `report_complete` | 최종 완료를 보고한다. |

## Execution Workflow

| 주체 | 역할 |
|---|---|
| User | Halt 또는 completion report를 받는다. |
| Root agent | CLI가 반환한 current task만 구현하고 verification을 실제로 실행한다. |
| `co` CLI | Current task, repair boundary, halt, completion을 `root_action`으로 반환하고 evidence state를 기록한다. |

기본 흐름은 아래와 같다.

```text
co flow next
execute_task 또는 repair_task 수행
verification 실행
co flow evidence
다음 root_action 처리
반복
```

## Evidence 기록

Verification output은 아래 형태로 기록한다.

```bash
<command> 2>&1 | ~/.codex/skills/coplan/scripts/co flow evidence \
  --step <step-id> \
  --command "<command>" \
  --exit-code <code> \
  --success true|false \
  --stdin
```

`--success true`는 검증 명령이 task의 성공 신호를 만족했다는 뜻이다.
`--success false`는 실패 output을 기록하고 `repair_task` 경계로 돌아가야 한다는 뜻이다.

## Repair와 Halt

Task metadata가 현재 구현 현실과 맞지 않지만 사용자-facing contract는 바뀌지 않는 경우에만 repair를 사용한다.

```bash
~/.codex/skills/coplan/scripts/co flow repair \
  --field <files|implementation_notes|verification path> \
  --reason "<reason>" \
  --set|--add|--remove <yaml-value>
```

사용자 결정이나 외부 환경 때문에 더 진행할 수 없으면 halt한다.

```bash
~/.codex/skills/coplan/scripts/co flow halt \
  --kind user_decision|external_environment \
  --reason "<reason>"
```

## 금지 사항

- Task를 직접 claim, complete, skip, reorder, finish하지 않는다.
- `plan.yaml`, `tasks.yaml`, `status.yaml`, `notes.yaml`, `evidence.yaml`을 직접 수정하지 않는다.
- 현재 task 밖의 source file이나 behavior를 임의로 넓히지 않는다.
- Acceptance criteria, non-goals, dependency, task order를 바꾸지 않는다.

## 보고 기준

- `report_complete`이면 최종 보고 첫 줄은 정확히 `최종 완료 🎉`로 쓴다.
- 중간에 멈추면 현재 `root_action.type` 또는 `root_action.halt`를 보고한다.
- 실행한 검증 명령과 성공/실패 결과를 짧게 보고한다.
