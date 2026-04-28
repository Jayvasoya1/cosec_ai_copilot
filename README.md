# COSEC AI Copilot 🚀

## 1. Problem Statement

Access control systems like Matrix COSEC devices are powerful but difficult to operate.

To perform even simple tasks (like adding a user or assigning access), users must:

* Navigate complex multi-layer menus
* Understand technical configuration steps
* Read long documentation/manuals
* Use exact parameter names
* Execute multiple steps in correct order

### ❌ Challenges Faced

* Steep learning curve for non-technical users
* Time-consuming operations
* High chance of misconfiguration
* Dependency on trained personnel
* Poor user experience

### Real Example Problem

> “Assign a user to a biometric device”

This involves:

* Creating user
* Setting credentials
* Assigning access group
* Configuring device mapping

👉 All through complex UI or API calls.

---

## 2. Proposed Solution

We built an **AI-powered Copilot system** that allows users to control COSEC devices using **simple natural language**.

### ✅ Core Idea

Instead of:

```
http://deviceIP/device.cgi/users?action=set&user-id=101&name=Ravi
```

User can simply type:

```
Add user Ravi with id 101
```

---

### 🧠 What Our System Does

* Understands user intent using AI
* Extracts required parameters
* Handles missing inputs intelligently
* Converts text into API commands
* Executes device configuration automatically

---

### 🎯 Goal

> Make access control systems usable by **anyone**, not just trained engineers.

---

## 3. What Data We Have (Very Important)

We are working with **COSEC Device API Documentation**.

### 📄 Nature of Data

* Large structured technical document (~200 pages)
* Divided into multiple **groups**
* Each group contains:

  * API endpoints
  * Parameters
  * Mandatory fields
  * Optional fields
  * Constraints and rules

---

### 📦 Example Group: `users`

#### API Format:

```
/device.cgi/users?action=<action>&param=value
```

---

### Supported Actions:

#### 1. SET (Add / Update User)

* Required:

  * `user-id`
  * `name`
* Optional:

  * `user-active`
  * `vip`
  * `user-pin`
  * `card1`
  * `user-group`
  * etc.

---

#### 2. GET (Fetch User Info)

#### 3. DELETE (Remove User)

---

### ⚠️ Constraints in Data

* Only one user can be modified at a time
* Some parameters depend on others
* Different actions require different fields
* Strict parameter naming required
* Device-specific behavior exists

---

### ❗ Important Insight

This data is:

* Too large for direct LLM input
* Highly structured
* Requires validation and control

---

## 4. Key Technical Challenge

### ❌ Wrong Approach

* Sending full API documentation to AI
* Letting AI generate full API calls

Problems:

* Token limits
* Low accuracy
* Uncontrolled outputs
* Hard to scale

---

### ✅ Our Approach (Correct)

We **separate responsibilities**:

| Component | Responsibility         |
| --------- | ---------------------- |
| AI Model  | Understand user intent |
| Backend   | Apply API logic        |
| Schema    | Store API rules        |
| Executor  | Call device            |

---

## 5. System Architecture

```
User Input (Natural Language)
        ↓
LLM (Intent Detection)
        ↓
Planner (Split multi-step tasks)
        ↓
Router (Select handler)
        ↓
Handler (Group logic)
        ↓
Schema (API rules validation)
        ↓
Parameter Resolver (fill missing + memory)
        ↓
API Builder
        ↓
Device API Call
        ↓
Response Builder
        ↓
User Output
```

---

## 6. Flow Explanation (Step-by-Step)

### Step 1: User Input

```
Add user Ravi with id 101
```

---

### Step 2: AI (Intent Detection)

```
{
  "tasks": [
    {
      "intent": "add_user",
      "parameters": {
        "name": "Ravi",
        "user_id": "101"
      }
    }
  ]
}
```

---

### Step 3: Planner

Handles multiple tasks:

```
Add Ravi and delete user 55
```

→ Split into 2 tasks

---

### Step 4: Router

Maps intent:

```
add_user → user_handler
```

---

### Step 5: Handler

Maps to API group:

```
users + action=set
```

---

### Step 6: Schema Validation

Checks:

* Required fields present?
* Valid structure?

---

### Step 7: Parameter Resolver

* Fills missing data
* Uses memory
* Handles optional fields

---

### Step 8: API Builder

```
/device.cgi/users?action=set&user-id=101&name=Ravi
```

---

### Step 9: Execution

* Sends HTTP request
* Or mock response (demo mode)

---

### Step 10: Response

```
✅ User Ravi added successfully
```

---

## 7. Key Features Implemented

### ✅ Natural Language Commands

* No need to remember API syntax

---

### ✅ Multi-Step Execution

```
Add Ravi and delete user 55
```

---

### ✅ Smart Questioning

```
User: Add Ravi
System: Please provide user ID
```

---

### ✅ Context Memory

```
User: Add Ravi
User: 101
```

→ System remembers previous input

---

### ✅ Modular Design

* Easy to add new groups:

  * door_handler
  * log_handler
  * credential_handler

---

## 8. Tech Stack Used

### 🧠 AI Layer

* OpenAI (GPT-4o-mini)

---

### 🐍 Backend

* Python

---

### 🌐 API Framework

* FastAPI

---

### 🔌 Device Communication

* HTTP (requests library)

---

### ⚙️ Config Management

* python-dotenv

---

## 9. Design Principles

### 🔑 Separation of Concerns

* AI → language understanding
* Backend → logic & execution

---

### 🔑 Schema-Driven Design

* API rules stored in structured format
* Not hardcoded in AI

---

### 🔑 Extensibility

* Add new features without breaking system

---

### 🔑 Controlled Execution

* No direct AI → API calls
* Always validated

---

## 10. Current Scope (What We Built)

### ✅ Implemented

* User Management:

  * Add user
  * Delete user
  * Update user

---

### 🚧 Not Yet Implemented

* Door configuration
* Credential management
* Access assignment
* Logs and monitoring

---

## 11. Future Scope

* Add all API groups (doors, logs, alarms)
* Replace mock with real device integration
* Multi-user session memory
* Role-based access control
* UI dashboard (chat interface)
* Offline / local LLM support

---

## 12. One-Line Summary

> We built an AI Copilot that converts simple English commands into validated API actions to fully control access control devices.

---

## 13. Final Conclusion

This system transforms:

❌ Complex technical operations
➡️ into
✅ Simple human interactions

---

## 14. Current Solution Summary

Currently, our system:

* Uses AI only for intent detection
* Uses structured schemas for API logic
* Supports multi-step commands
* Handles missing inputs dynamically
* Maintains conversation context
* Executes device commands via HTTP

---

## 15. Why This is Powerful

* Removes need for training
* Reduces human errors
* Saves time
* Improves usability
* Scalable to full device control

---

## 16. Demo Example

```
User: Add Ravi
System: Please provide user ID

User: 101
System: ✅ User Ravi added

User: Delete him
System: ✅ User deleted
```

---

# 🚀 End of README
