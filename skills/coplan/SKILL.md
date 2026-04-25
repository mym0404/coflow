---
name: coplan
description: 사용자 요청을 `co flow`로 실행 가능한 plan bundle로 정리하는 root-agent용 planner 스킬.
---

# Coplan

너는 이 스킬을 실행하는 root agent다.

목표는 사용자 요청을 `co flow`에 전달하고, CLI가 돌려주는 `root_action`을 수행해서 실행 가능한 `.agents/plan/{plan-id}/` plan bundle을 만드는 것이다. 이 스킬을 사용하는 동안 실제 source code 구현은 하지 않는다.

## 핵심 계약

- `co flow`가 다음 행동을 `root_action`으로 반환한다.
- 모든 `co flow` 응답은 YAML이며 `contract_version`, `mode`, `phase`, `root_action`을 확인한다.
- Root agent는 반환된 `root_action` 하나만 수행한다.
- 사용자에게 물어야 할 내용은 `root_action.question` 그대로 묻는다.
- 사용자에게 보여줄 draft는 `root_action.draft` 그대로 보여준다.
- 사용자 답변, approval, feedback은 `co flow respond --stdin`으로 전달한다.
- Bundle file은 CLI가 쓰는 실행 상태다. Root agent가 직접 수정하지 않는다.
- `root_action.type`이 executor action으로 바뀌면 `coplan`을 끝내고 `coexec`로 전환한다.

## Flow Stdout

`co flow`는 root agent가 처리해야 할 정보만 YAML로 반환한다.

```yaml
contract_version: '1'
mode: planner|executor|halted|complete|error
phase: drafting
root_action:
  type: continue_flow|ask_user|present_draft|execute_task|repair_task|report_halt|report_complete|report_error
```

`phase`는 active plan 상태다.
에러도 `mode: error`와 `root_action.type: report_error`로 표현된다.
항상 `root_action.type`에 맞는 행동 하나만 수행한다.

Planner에서 주로 받는 `root_action` 모양은 아래와 같다.

```yaml
root_action:
  type: continue_flow
  message: Run `co flow next` to continue planning.
  next_command: co flow next
```

```yaml
root_action:
  type: ask_user
  question: 사용자에게 그대로 전달할 질문
  response_command: co flow respond --stdin
```

```yaml
root_action:
  type: present_draft
  draft: 사용자에게 그대로 보여줄 draft 본문
  response_command: co flow respond --stdin
```

```yaml
root_action:
  type: report_error
  message: CLI가 보고한 에러 내용
```

`execute_task` 또는 `repair_task`가 오면 planning이 끝났거나 execution 경계에 도달한 것이다. 이 스킬을 끝내고 `coexec` 스킬로 전환한다.

## 시작

새 plan은 아래 명령으로 시작한다.

```bash
~/.codex/skills/coplan/scripts/co flow init --plan-id <stable-kebab-id> --title "<title>"
```

그다음 아래 명령으로 다음 경계를 받는다.

```bash
~/.codex/skills/coplan/scripts/co flow next
```

## Root Action 처리

| `root_action.type` | 수행 |
|---|---|
| `continue_flow` | `root_action.next_command`를 실행한다. 보통 `co flow next`다. |
| `ask_user` | `root_action.question`을 그대로 사용자에게 묻고 답변을 `co flow respond --stdin`으로 전달한다. |
| `present_draft` | `root_action.draft`를 그대로 사용자에게 보여주고 approval 또는 feedback을 `co flow respond --stdin`으로 전달한다. |
| `execute_task` | Planning이 끝난 상태다. `coexec`로 전환한다. |
| `repair_task` | Execution 경계다. `coexec`로 전환한다. |
| `report_halt` | Halt 내용을 사용자에게 보고한다. |
| `report_complete` | 완료 내용을 사용자에게 보고한다. |
| `report_error` | `root_action.message`를 사용자에게 보고하고 멈춘다. |

## Planning Workflow

| 주체 | 역할 |
|---|---|
| User | 요청, 답변, draft approval 또는 feedback을 제공한다. |
| Root agent | `co flow`를 실행하고, 질문과 draft를 사용자에게 전달하고, 사용자 응답을 CLI로 되돌려 보낸다. |
| `co` CLI | 다음 root boundary를 `root_action`으로 반환하고 bundle state를 기록한다. |

기본 흐름은 아래와 같다.

```text
co flow init
co flow next
root_action 처리
co flow respond --stdin 또는 co flow next
반복
```

Planning이 끝나면 `root_action.type: execute_task`가 반환되고, root agent는 `coexec`로 전환한다.
인터뷰가 충분해 보여도 `co flow`가 숨은 가정 확인 질문을 `ask_user`로 반환할 수 있다. 이 경우에도 다른 질문과 동일하게 그대로 묻고 답변을 전달한다.

## 명령 제한

Planning 중 사용하는 flow command는 아래뿐이다.

```bash
~/.codex/skills/coplan/scripts/co flow init --plan-id <id> --title "<title>" [--replace]
~/.codex/skills/coplan/scripts/co flow next
~/.codex/skills/coplan/scripts/co flow respond --stdin
~/.codex/skills/coplan/scripts/co flow status
```

필요하면 read-only/diagnostic command는 사용할 수 있다.

```bash
~/.codex/skills/coplan/scripts/co current
~/.codex/skills/coplan/scripts/co show --file draft|plan|tasks|status|notes|evidence
~/.codex/skills/coplan/scripts/co doctor
```

## 금지 사항

- `draft.md`, `plan.yaml`, `tasks.yaml`, `planning_context.yaml`, `interview.yaml`, `status.yaml`, `notes.yaml`, `evidence.yaml`을 직접 수정하지 않는다.
- `root_action`에 없는 다음 단계를 임의로 만들지 않는다.
- Planning 중 source code를 구현하지 않는다.
- 명시적으로 요청받기 전에는 commit, branch, push, PR을 만들지 않는다.

## 보고 기준

- 현재 plan이 생겼으면 `co current` 기준으로 active plan을 보고한다.
- 사용자 입력이 필요한 상태면 질문 또는 draft만 보여준다.
- 중간에 멈추면 `report_error` 또는 `report_halt` 내용을 그대로 설명한다.
