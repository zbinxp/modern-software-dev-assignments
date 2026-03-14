# Week 6 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## Instructions

Fill out all of the `TODO`s in this file.

## Submission Details

Name: **TODO** \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do. 


## Brief findings overview 
> TODO

## Fix #1 Code Injection with FastAPI
a. File and line(s)
> backend/app/routers/notes.py:104

b. Rule/category Semgrep flagged
> Critical severity

c. Brief risk description
> The application might dynamically evaluate untrusted input, which can lead to a code injection vulnerability. An attacker can execute arbitrary code, potentially gaining complete control of the system. To prevent this vulnerability, avoid executing code containing user input. If this is unavoidable, validate and sanitize the input, and use safe alternatives for evaluating user input.

d. Your change (short code diff or explanation, AI coding tool usage)
> Security fix: Removed dangerous eval() usage that allowed code injection.

e. Why this mitigates the issue
> eval() code is removed, so the issue is gone.

## Fix #2 SQL Injection with SQLAlchemy
a. File and line(s)
> backend/app/routers/notes.py:72

b. Rule/category Semgrep flagged
> Critical severity

c. Brief risk description
> Untrusted input might be used to build a database query, which can lead to a SQL injection vulnerability. An attacker can execute malicious SQL statements and gain unauthorized access to sensitive data, modify, delete data, or execute arbitrary system commands. Use the SQLAlchemy ORM provided functions to build SQL queries instead to avoid SQL injection.

d. Your change (short code diff or explanation, AI coding tool usage)
> Security fix: Use parameterized queries instead of f-string interpolation to prevent SQL injection (CWE-89)

e. Why this mitigates the issue
> parameterized queries using :query placeholder with bound parameters avoid SQL Injection

## Fix #3 SQL Injection with FastAPI
a. File and line(s)
> Tbackend/app/routers/notes.py:36DO

b. Rule/category Semgrep flagged
> Critical severity

c. Brief risk description
> Untrusted input might be used to build a database query, which can lead to a SQL injection vulnerability. An attacker can execute malicious SQL statements and gain unauthorized access to sensitive data, modify, delete data, or execute arbitrary system commands. The driver API has the ability to bind parameters to the query in a safe way.

d. Your change (short code diff or explanation, AI coding tool usage)
> use whitelist `if sort_field in ALLOWED_SORT_FIELDS:` to replace old statement `if hasattr(Note, sort_field):`

e. Why this mitigates the issue
> malicious code would not pass the condition check