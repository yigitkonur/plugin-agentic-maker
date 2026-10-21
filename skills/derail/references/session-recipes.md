# Reading a session that already exists, with jq

> Read when: you have a session id or a transcript file of Claude Code, Codex or agy and want its events, its last message, its token use or its failed commands without going through `agentic-maker`.

`agentic-maker normalize session:<id>` (or `herdr:<pane>`) does all of this and writes `trace.md` with the `[n]` references the reader cites. The commands below are the same reading as plain `jq`, for a question the plugin does not answer. The transcript formats are internal to each harness and change between versions: these were run on Claude Code 2.1.304, codex-cli 0.163 and the Antigravity CLI of October 2026, and the plugin's Python adapters produce the same events from the same files (143, 28 and 20 events, no difference).

## Where the record is

| Harness | File |
|---|---|
| Claude Code | `~/.claude/projects/<working directory with / as ->/<session id>.jsonl`; a subagent: `<session id>/subagents/agent-<id>.jsonl` |
| Codex | `~/.codex/sessions/YYYY/MM/DD/rollout-<time>-<session id>.jsonl` (older ones under `archived_sessions/`) |
| agy | `~/.gemini/antigravity-cli/brain/<session id>/.system_generated/logs/transcript_full.jsonl`; **not** `transcript.jsonl`, which cuts every `content` at about 4096 characters |

herdr knows a pane's session: `herdr agent get <pane>` has `agent_session.value` for Claude and agy. For a Codex pane herdr 0.9.5 reported none; its status line prints the id.

## One event per line, in the plugin's shape

Each program prints `{role, kind, name, args, text, is_error}` with `kind` one of `text`, `thinking`, `tool_use`, `tool_result`. Text is never trimmed. Save a program as `claude.jq` and run `jq -c -f claude.jq <file>`; the agy one reads all lines at once: `jq -c -n -f agy.jq <file>`.

Claude Code (a result's non-text blocks are kept as compact JSON; a thinking block is often empty, because only its signature is stored):

```
select(.type=="user" or .type=="assistant") | . as $l | .message.content as $c
| if ($c|type)=="string" then {role:$l.type,kind:"text",name:null,args:null,text:$c,is_error:null}
  else $c[] | if .type=="text" then {role:$l.type,kind:"text",name:null,args:null,text:.text,is_error:null}
  elif .type=="thinking" then {role:$l.type,kind:"thinking",name:null,args:null,text:.thinking,is_error:null}
  elif .type=="tool_use" then {role:"assistant",kind:"tool_use",name:.name,args:.input,text:null,is_error:null,id:.id}
  elif .type=="tool_result" then {role:"tool",kind:"tool_result",name:null,args:null,id:.tool_use_id,is_error:(.is_error==true),
     text:(if (.content|type)=="string" then .content else ([.content[]?|if .type=="text" then .text else tojson end]|join("\n")) end)}
  else {role:$l.type,kind:"other",name:.type,args:null,text:null,is_error:null} end end
```

Codex (`developer` messages are the harness's own instructions to the agent; the exit code of a command is only in the `CommandExecution` item):

```
def txt: if type=="string" then . elif type=="array" then map(.text // tojson)|join("\n") else tojson end;
.payload as $p
| if .type=="response_item" then
   if $p.type=="message" then {role:$p.role,kind:"text",name:null,args:null,text:($p.content|txt),is_error:null}
   elif $p.type=="reasoning" then {role:"assistant",kind:"thinking",name:null,args:null,text:([$p.summary[]?.text]|join("\n")),is_error:null}
   elif $p.type=="function_call" then {role:"assistant",kind:"tool_use",name:$p.name,args:($p.arguments|try fromjson catch {input:.}),text:null,is_error:null,id:$p.call_id}
   elif $p.type=="custom_tool_call" then {role:"assistant",kind:"tool_use",name:$p.name,args:{input:$p.input},text:null,is_error:null,id:$p.call_id}
   elif ($p.type|test("^(function|custom_tool)_call_output$")) then ($p.output|txt) as $t|{role:"tool",kind:"tool_result",name:null,args:null,text:$t,id:$p.call_id,is_error:($t|test("^(Error:|FAILED|Script failed)|Process exited with code [1-9]";"m"))}
   else empty end
  elif .type=="event_msg" and $p.type=="item_completed" and $p.item.type=="CommandExecution" then
   {role:"tool",kind:"tool_result",name:"CommandExecution",args:{command:$p.item.command},text:$p.item.aggregated_output,is_error:($p.item.exit_code!=0),exit:$p.item.exit_code}
  else empty end
```

agy (it numbers no tool calls: a result belongs to the oldest call still waiting):

```
def ev(r;k;n;a;t;e):{role:r,kind:k,name:n,args:a,text:t,is_error:e};
foreach inputs as $s ({q:[],out:[]};
 if ($s.type=="USER_INPUT" or $s.type=="USER_MESSAGE") then .q=[]|.out=[ev("user";"text";null;null;$s.content;null)]
 elif ($s.type=="PLANNER_RESPONSE" or $s.type=="ASSISTANT_STEP") then
   .out=[(if ($s.thinking//"")!="" then ev("assistant";"thinking";null;null;$s.thinking;null) else empty end),
         (if ($s.content//"")!="" then ev("assistant";"text";null;null;$s.content;null) else empty end),
         ($s.tool_calls[]?|ev("assistant";"tool_use";.name;.args;null;null))] | .q+=[$s.tool_calls[]?.name]
 elif ($s.type=="GENERIC" or $s.type=="TOOL_STEP") then ($s.content//"") as $c
   | ([$c|capture("exited with code (?<x>-?[0-9]+)")]|first|.x//null|if . then tonumber else null end) as $x
   | .out=[ev("tool";"tool_result";.q[0];null;$c;($s.status=="ERROR" or $s.status=="INVALID" or (($s.error//"")!="") or ($x!=null and $x!=0) or ($c|startswith("Error:"))))] | .q=.q[1:]
 else .out=[] end; .out[])
```

## Questions that need one line

```
# Claude Code: the last thing the agent said
jq -rs '[.[]|select(.type=="assistant")|.message.content[]?|select(.type=="text")|.text]|last' <file>
# tokens per model, counted once per API response (a response is written once per content block, each with the full usage)
jq -cs '[.[]|select(.type=="assistant" and .message.usage!=null and .message.model!="<synthetic>" and .isSidechain!=true)]|group_by(.message.id)|map(last)|group_by(.message.model)|map({model:.[0].message.model,responses:length,input:(map(.message.usage.input_tokens//0)|add),output:(map(.message.usage.output_tokens//0)|add),cache_read:(map(.message.usage.cache_read_input_tokens//0)|add),cache_create:(map(.message.usage.cache_creation_input_tokens//0)|add)})[]' <file>
# the running cost in dollars, if the record has it
jq -c 'select(.type=="cost-state")|{totalCostUSD}' <file> | tail -1
# failed tool calls, with the tool's name
jq -cs '([.[]|.message.content?|arrays|.[]|select(.type=="tool_use")|{(.id):.name}]|add//{}) as $n|.[]|select(.type=="user")|.message.content?|arrays|.[]|select(.type=="tool_result" and .is_error==true)|{id:.tool_use_id,name:$n[.tool_use_id],text:(if (.content|type)=="string" then .content else ([.content[]?|if .type=="text" then .text else tojson end]|join("\n")) end)}' <file>

# Codex: the final answer (a turn that ended early has none), commands that failed, tokens per model
jq -rs 'map(select(.type=="response_item" and .payload.type=="message" and .payload.role=="assistant" and .payload.phase=="final_answer"))|last.payload.content|map(.text)|join("\n")' <file>
jq -c 'select(.type=="event_msg" and .payload.type=="item_completed" and .payload.item.type=="CommandExecution" and .payload.item.exit_code!=0)|.payload.item|{command,exit_code,status}' <file>
jq -cs '(map(select(.type=="turn_context")|{(.payload.turn_id):.payload.model})|add) as $m|map(select(.type=="token_usage_record"))|unique_by(.payload.response_id)|group_by($m[.payload.turn_id]//"unknown")|map({model:($m[.[0].payload.turn_id]//"unknown"),responses:length,input:(map(.payload.usage.input_tokens)|add),cached_input:(map(.payload.usage.cached_input_tokens)|add),output:(map(.payload.usage.output_tokens)|add)})[]' <file>

# agy: the final answer, tokens (the transcript names no model)
jq -rs 'map(select((.type=="PLANNER_RESPONSE" or .type=="ASSISTANT_STEP") and ((.content//"")!="")))|last.content' <file>
jq -cs 'map(select(.type=="PLANNER_RESPONSE" or .type=="ASSISTANT_STEP"))|{responses:length,input:(map(.input_tokens//0)|add),output:(map(.output_tokens//0)|add),cache_read:(map(.cache_read_tokens//0)|add)}' <file>
```

A quote that a reader will have verified against these events has to match them exactly, so do not trim, re-wrap or decode anything you copy from a recipe's output.
