# Architecture Diagrams

## Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INPUT (Natural Language)                │
│              "Add user John with id 101"                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  1. INTENT PARSER                  │
        │  (app/core/intent_parser.py)       │
        │                                    │
        │  • Call OpenAI LLM                 │
        │  • Parse JSON response             │
        │  • Validate structure              │
        │  • Extract tasks                   │
        └────────────────────────────────────┘
          │
          │ (Can raise IntentParsingError)
          ▼
        ┌────────────────────────────────────┐
        │  2. PLANNER                        │
        │  (app/core/planner.py)             │
        │                                    │
        │  • Extract tasks from intent       │
        │  • Ready for multi-step planning   │
        └────────────────────────────────────┘
          │
          │ {intent: "add_user", parameters: {...}}
          ▼
        ┌────────────────────────────────────┐
        │  3. ROUTER                         │
        │  (app/core/router.py)              │
        │                                    │
        │  • Lookup handler by intent        │
        │  • Route to handler                │
        └────────────────────────────────────┘
          │
          │ (Can raise RouterError)
          ▼
        ┌────────────────────────────────────┐
        │  4. HANDLER                        │
        │  (handlers/user_handler.py)        │
        │                                    │
        │  • Map intent to action            │
        │  • Transform parameters            │
        │  • Resolve missing params          │
        │  • Return group + params           │
        └────────────────────────────────────┘
          │
          │ (Can return need_input)
          ├─► {need_input: True, missing: [...]}
          │   │
          │   └─► Ask user for missing params
          │
          └─► {group: "users", params: {...}}
              │
              ▼
            ┌────────────────────────────────────┐
            │  5a. EXECUTOR                      │
            │  (app/core/executor.py)            │
            │                                    │
            │  • API Builder: build URL          │
            │  • Device API: call COSEC          │
            │  • Handle errors                   │
            │  • Return result                   │
            └────────────────────────────────────┘
              │
              │ (Can raise APIBuildError, DeviceAPIError)
              ▼
            ┌────────────────────────────────────┐
            │  5b. RESPONSE BUILDER              │
            │  (app/core/response_builder.py)    │
            │                                    │
            │  • Format results                  │
            │  • Build user message              │
            │  • Aggregate success/failure       │
            └────────────────────────────────────┘
              │
              ▼
        ┌─────────────────────────────────────────────────────────┐
        │             RESPONSE TO USER                            │
        │  {                                                      │
        │    "status": "success",                                 │
        │    "message": " User added successfully",             │
        │    "details": {...}                                     │
        │  }                                                      │
        └─────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
Any Exception
    │
    ├─► IntentParsingError
    │   │
    │   └─► Handler catches & logs
    │       │
    │       └─► Returns error response
    │
    ├─► RouterError
    │   │
    │   └─► No handler found for intent
    │       │
    │       └─► Returns error response
    │
    ├─► ValidationError / MissingParametersError
    │   │
    │   ├─► If user input needed
    │   │   └─► Ask for missing fields
    │   │
    │   └─► If validation fails
    │       └─► Return validation error
    │
    ├─► APIBuildError
    │   │
    │   └─► URL building failed
    │       │
    │       └─► Return error with details
    │
    └─► DeviceAPIError
        │
        ├─► Authentication failed
        ├─► Device unreachable
        ├─► Timeout
        │
        └─► Return error with retry info
```

---

## Schema Registry Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    SCHEMA REGISTRY                             │
│            (app/schemas/registry.py)                           │
│                                                                │
│  ┌──────────────────────────────────────────────────┐          │
│  │ register_schemas()                               │          │
│  │                                                  │          │
│  │  ├─ "users" → UserSchema                         │          │
│  │  ├─ "devices" → DeviceSchema (future)            │          │
│  │  ├─ "accessgroup" → AccessGroupSchema (future)   │          │
│  │  └─ "credentials" → CredentialSchema (future)    │          │
│  │                                                  │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                │
│  Methods:                                                      │
│  ├─ get(group_name) → Schema                                  │
│  ├─ list_groups() → [group_names]                             │
│  ├─ is_registered(group_name) → bool                          │
│  └─ get_actions(group_name) → {actions}                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
        │
        ├──────────────────┬──────────────────┬──────────────────┐
        ▼                  ▼                  ▼                  ▼
    ┌─────────────┐   ┌──────────────┐   ┌─────────────┐   ┌──────────────┐
    │ UserSchema  │   │DeviceSchema  │   │AccessGroup  │   │Credentials   │
    │(BaseSchema) │   │(BaseSchema)  │   │Schema       │   │Schema        │
    │             │   │              │   │(BaseSchema) │   │(BaseSchema)  │
    │ ├─ actions  │   │ ├─ actions   │   │ ├─ actions  │   │ ├─ actions   │
    │ ├─ validate │   │ ├─ validate  │   │ ├─ validate │   │ ├─ validate  │
    │ └─ transform│   │ └─ transform │   │ └─ transform│   │ └─ transform │
    └─────────────┘   └──────────────┘   └─────────────┘   └──────────────┘
```

---

## Handler Registry Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   HANDLER REGISTRY                             │
│            (app/core/router.py)                                │
│                                                                │
│  ┌──────────────────────────────────────────────────┐          │
│  │ register_pattern()                               │          │
│  │                                                  │          │
│  │  "user_" → handle_user_intent                    │          │
│  │  "device_" → handle_device_intent (future)       │          │
│  │  "accessgroup_" → handle_access_group_intent     │          │
│  │                                                  │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                │
│  Intent Matching:                                              │
│  │                                                             │
│  ├─ "add_user" → matches "user_" → UserHandler               │
│  ├─ "delete_user" → matches "user_" → UserHandler            │
│  ├─ "add_device" → matches "device_" → DeviceHandler         │
│  └─ "add_access_group" → matches "accessgroup_" → AGHandler  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Parameters

```
LLM Output                Handler Transform            API Call
──────────                ──────────────────           ────────

{                         ↓                            ↓
  "name": "John"  ──┐
  "user_id": "101" ◄┼─► map_to_api ──┐    ┌─────────────────────┐
  ...               │                 └──► │ "name": "John"      │
}                   │                      │ "user-id": "101"    │
                    │                      │ "action": "set"     │
                    │                      │ ...                 │
                    │                      └─────────────────────┘
                    │                               │
                    │                               ▼
                    │                      /device.cgi/users?...
                    │
                    └─────────────────────────────────┘
```

---

## Memory Context Usage

```
First Request
────────────
User: "Add user John with id 101"
       │
       └─► Handler resolves params
           │
           └─► Save to memory:
               memory["last_user"] = {
                 "user-id": "101",
                 "name": "John"
               }


Second Request
──────────────
User: "Delete user"
       │
       └─► Handler checks memory
           │
           ├─► Memory has "last_user"
           │
           └─► Automatically uses: user-id = "101"
               (No need to ask user again!)


Flow:
    Handler                  Memory
       │                       │
       ├─ merge(memory_ctx    │
       │   + new_params)      │
       │                       │
       ├─ check missing       │
       │                       │
       ├─ if all found        │
       │  └─ save to memory ──┼──► memory["last_user"] = {...}
       │                       │
       └─ return params
```

---

## Multi-Task Execution

```
User Input
  │
  └─► LLM Parsing
       │
       └─► Multiple Tasks
           │
           ├─ Task 1: Add user John
           ├─ Task 2: Add user Jane
           └─ Task 3: Create access group
               │
               ▼
           Executor (sequential)
               │
               ├─► Task 1: Router → Handler → API
               │   │
               │   └─ Result 1 
               │
               ├─► Task 2: Router → Handler → API
               │   │
               │   └─ Result 2 
               │
               ├─► Task 3: Router → Handler → API
               │   │
               │   └─ Result 3  (or error)
               │       │
               │       ▼ (stop if need_input)
               │
               └─ Aggregate Results
                   │
                   ├─ Successful: 3
                   ├─ Failed: 0
                   └─ Messages: [" Task 1...", ...]
```

---

## Logging Coverage

```
Request Flow                         Logging Point
───────────                          ─────────────

1. User Input               → log_event("INTENT_PARSING_START")
   ↓
2. LLM Call                 → log_event("LLM_CALL", {url, params})
   ↓
3. Intent Parsed            → log_intent(user_input, parsed_intent)
   ↓
4. Tasks Planned            → log_event("TASKS_PLANNED", {count, tasks})
   ↓
5. Routing                  → log_event("ROUTING", {intent, handler})
   ↓
6. Handler Processing       → log_event("HANDLER_EXECUTION", {result})
   ↓
7. Param Resolution         → log_parameter_resolution(params, missing, partial)
   ↓
8. API Building             → log_event("API_BUILDING", {group, params})
   ↓
9. Device API Call          → log_api_call(url, params, response)
   ↓
10. Execution Complete      → log_task_execution(task, handler, result)
    ↓
11. Response Built          → log_event("RESPONSE_BUILT", {status, code})
    ↓
12. Sent to User            → Response object


Debug Mode (DEBUG_MODE=True):
├─ Trace every function call
├─ Log all variable values
├─ Show memory context
├─ Full error stack traces
└─ Detailed timing information
```
