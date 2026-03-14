# REPL Mode

The `repl` subcommand starts an interactive Read-Eval-Print Loop for running multiple queries against a loaded graph without the overhead of reloading data from disk each time.

---

## Starting the REPL

```bash
# Using stored account ID
pmapper --account 123456789012 repl

# Using live credentials
pmapper --profile my-profile repl
```

---

## Using the REPL

Once started, the REPL loads the graph into memory and presents a prompt. You can type queries using the same syntax as the `query` subcommand:

```
PMapper REPL for account 123456789012
Type 'exit' or 'quit' to leave.
> who can do iam:CreateUser
  user/admin CAN CALL iam:CreateUser WITH *
  role/AdminRole CAN CALL iam:CreateUser WITH *
> can arn:aws:iam::123456789012:user/dev do s3:GetObject with arn:aws:s3:::secret-bucket/*
  user/dev CANNOT CALL s3:GetObject WITH arn:aws:s3:::secret-bucket/*
> preset privesc *
  ...
> exit
```

---

## Query Syntax

The REPL supports the same query patterns as `pmapper query`:

| Pattern | Example |
|---------|---------|
| `who can do <action>` | `who can do iam:CreateUser` |
| `who can do <action> with <resource>` | `who can do s3:GetObject with arn:aws:s3:::bucket/*` |
| `can <principal> do <action>` | `can arn:aws:iam::123456789012:user/dev do iam:CreateUser` |
| `can <principal> do <action> with <resource>` | `can arn:aws:iam::123456789012:role/app do s3:PutObject with *` |
| `preset <name> <principal>` | `preset privesc *` |
| `exit` or `quit` | Exit the REPL |

---

## When to Use the REPL

| Scenario | Best Tool |
|----------|-----------|
| Exploring an account interactively | **REPL** ✅ |
| Running a single query | `query` or `argquery` |
| Scripting multiple queries | `argquery` in a loop |
| Iterating through different actions | **REPL** ✅ |
| Demonstrating PMapper to stakeholders | **REPL** ✅ |

The REPL is especially useful during **penetration tests** and **incident response** when you need to quickly explore what different principals can do.

---

## Tips

- The REPL keeps the graph in memory, so it's significantly faster than running separate `pmapper query` commands for each question
- Use `preset privesc *` as your first query to get a quick overview of escalation risks
- The REPL does not currently support `argquery`-style flags (conditions, resource policies, etc.)

---

[← Analysis Commands](Analysis-Commands) | [Troubleshooting →](Troubleshooting)
