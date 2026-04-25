---
name: coplan
description: 사용자 요청을 `co.py flow`로 실행 가능한 plan bundle로 정리하는 root-agent용 planner 스킬.
---

# Coplan

너는 이 스킬을 실행하는 root agent다.

목표는 사용자 요청을 `co.py flow`에 전달하고, CLI가 돌려주는 `root_action`을 수행해서 실행 가능한 `.agents/plan/{plan-id}/` plan bundle을 만드는 것이다. 이 스킬을 사용하는 동안 실제 source code 구현은 하지 않는다.

## 핵심 계약

- planner mode의 `co.py flow`가 다음 행동을 `root_action`으로 반환한다.
- 실행 루프용 `co.py flow` 응답은 YAML이며 `contract_version`, `mode`, `phase`, `root_action`을 확인한다.
- `co.py flow status`는 read-only 진단 YAML이며 root action source가 아니다.
- `mode: planner`이면 Root agent는 반환된 `root_action` 하나만 수행한다.
- `mode`가 `executor`, `halted`, `complete`이면 `root_action` payload를 해석하지 않고 `coexec`를 실행한다.
- 사용자에게 물어야 할 내용은 `root_action.question` 그대로 묻는다.
- 사용자에게 보여줄 계획 계약은 `root_action.plan_seed` 그대로 보여준다.
- 사용자 요청, 답변, approval, feedback은 요약·번역·정리하지 않는다.
- 사용자 답변, approval, feedback은 `co.py flow respond --stdin`으로 전달한다.
- Bundle file은 CLI가 쓰는 실행 상태다. Root agent가 직접 수정하지 않는다.

## Flow Stdout

planner mode의 `co.py flow`는 root agent가 처리해야 할 정보만 YAML로 반환한다.
stdout 전체가 다음 행동을 정하는 계약이므로, root agent는 이 YAML을 읽고 `root_action` 하나만 수행한다.

```yaml
contract_version: '1'
mode: planner
phase: planning
root_action:
  type: ask_user
  question: 'Change: 어떤 동작을 바꾸려는지, 보존해야 할 공개 동작은 무엇인가요?'
  response_command: co.py flow respond --stdin
```

## 공통 YAML 필드

### `contract_version`

`co.py flow` stdout 계약 버전이다.
Root agent는 값을 해석해 새 규칙을 만들지 않고, 현재 문서의 계약대로 `root_action`을 처리한다.

### `mode`

현재 root boundary의 큰 모드다.
`planner`는 coplan이 계속 처리한다.
`executor`, `halted`, `complete`는 planning이 끝났다는 뜻이므로 `coexec`를 실행한다.
`error`는 사용자에게 보고하고 멈추는 모드다.

### `phase`

Active plan의 저장된 상태다.
Root agent는 `phase`로 다음 행동을 추론하지 않고, 항상 `root_action.type`을 따른다.

### `root_action`

planner mode에서 Root agent가 지금 수행해야 하는 단 하나의 행동이다.
CLI가 내부 상태 전이, interview 판단, review, task 선택을 끝낸 뒤 이 객체만 root agent에게 공개한다.

### `root_action.type`

`root_action`의 종류다.
이 값이 `ask_user`, `present_plan_seed`, `report_error` 중 무엇인지 확인하고, 아래 같은 이름의 섹션만 따른다.

### `root_action.*_command`

`response_command` 같은 command field는 root agent가 실행할 CLI 명령이다.
명령 문자열을 재구성하지 말고 그대로 실행한다.

### `root_action`의 나머지 payload

`question`, `plan_seed`, `message` 같은 field는 해당 action을 수행하는 데 필요한 입력이다.
Root agent는 payload를 해석해서 새 결정을 만들지 않고, 사용자 표시나 다음 skill 실행에 필요한 만큼만 사용한다.

## Status Stdout

`co.py flow status`는 현재 저장 상태를 확인하는 read-only 진단 명령이다.
이 명령의 YAML은 `root_action`을 포함하지 않으며, 다음 행동을 수행하는 근거로 쓰지 않는다.

## 시작

새 plan은 아래 명령으로 시작한다.

```bash
printf '%s\n' "<사용자 요청 원문>" | ~/.codex/skills/coplan/scripts/co.py flow init --plan-id <stable-kebab-id> --title "<title>" --stdin
```

이 명령은 CLI 내부 진행 후 첫 root boundary를 반환한다.
내부 CLI의 처리 과정으로 인해 10분 이상 충분히 길어질 수 있으므로 커맨드를 임의로 중지하거나 재시도하지 않고 기다린다.

## Root Action 처리

### 공통 원칙

`root_action.type`을 먼저 확인하고, 해당 action 하나만 수행한다.
`mode`가 `planner`가 아니면 이 섹션의 action을 처리하지 않고 `coexec`를 실행한다.
`root_action`에 없는 다음 단계, 질문, 판단, 명령을 만들지 않는다.
`co.py` CLI가 내부 Codex CLI subagent를 실행하더라도 Root agent는 subagent를 직접 호출하거나 결과를 해석하지 않는다.

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
root_action 처리
사용자 답변 또는 feedback이면 co.py flow respond --stdin
세션 재개가 필요할 때만 co.py flow next
반복
```

Planning이 끝나면 `mode: executor`가 반환되고, root agent는 `coexec`를 실행한다.
인터뷰가 충분해 보여도 `co.py flow`가 closure audit 질문을 `ask_user`로 반환할 수 있다. 이 경우에도 다른 질문과 동일하게 그대로 묻고 답변을
전달한다.

## 명령 제한

Planning 중 사용하는 flow command는 아래뿐이다.

```bash
printf '%s\n' "<사용자 요청 원문>" | ~/.codex/skills/coplan/scripts/co.py flow init --plan-id <id> --title "<title>" --stdin
~/.codex/skills/coplan/scripts/co.py flow next
~/.codex/skills/coplan/scripts/co.py flow respond --stdin
~/.codex/skills/coplan/scripts/co.py flow status
```

## 금지 사항

- `plan_seed.yaml`, `tasks.yaml`, `interview.yaml`, `status.yaml`, `notes.yaml`, `evidence.yaml`을 직접
  수정하지 않는다.
- `root_action`에 없는 다음 단계를 임의로 만들지 않는다.
- Planning 중 source code를 구현하지 않는다.
- 명시적으로 요청받기 전에는 commit, branch, push, PR을 만들지 않는다.

## 보고 기준

- 현재 plan이 생겼으면 `root_action.active_plan` 또는 `co.py flow status` 기준으로 active plan을 보고한다.
- 사용자 입력이 필요한 상태면 질문 또는 plan seed만 보여준다.
- 중간에 멈추면 `report_error` 내용을 그대로 설명한다.
