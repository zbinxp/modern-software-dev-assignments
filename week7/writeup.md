# Week 7 Write-up
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


## Task 1: Add more endpoints and validations
a. Links to relevant commits/issues
> [commits](https://github.com/zbinxp/modern-software-dev-assignments/pull/1/changes/cb0dc66d365538c0dfd9f74b17d1dc177e44b814)

b. PR Description
> 
```
## Description of the problem and your approach.
problem: notes don't support full CRUD operation
aproach:
- Add delete endpoint for note
- Add input validation for all endpoint
- AddXSS protection and error handling

## Summary of testing performed (include commands and results) and any added/updated tests.
`make test`
9 passed, 15 warnings in 0.29s

Added tests:
Unit tests for delete, validation (422), and 404 cases

## Notable tradeoffs, limitations, or follow-ups.
deleting a note maybe need permission to do it
```

c. Graphite Diamond generated code review
> Graphite found no issues


## Task 2: Extend extraction logic
a. Links to relevant commits/issues
> [pull request](https://github.com/opencane/modern-software-dev-assignments/pull/2)

b. PR Description
> 
```
## Summary
- Enhanced action item extraction with sophisticated pattern recognition (checkbox [ ], priority (A), @mentions, action verbs)
- Added entity extraction for assignees and due dates
- Added confidence scoring for pattern matches  
- Added comprehensive unit tests (36 tests)
- Added proper error handling for None/invalid inputs
- Maintained backward compatibility

## Test plan
- [x] Run `poetry run pytest backend/tests/test_extract.py` - all 36 tests pass
- [x] Verify backward compatibility with existing code
```

c. Graphite Diamond generated code review
> Graphite found no issues

## Task 3: Try adding a new model and relationships
a. Links to relevant commits/issues
> TODO

b. PR Description
> TODO

c. Graphite Diamond generated code review
> TODO

## Task 4: Improve tests for pagination and sorting
a. Links to relevant commits/issues
> TODO

b. PR Description
> TODO

c. Graphite Diamond generated code review
> TODO

## Brief Reflection 
a. The types of comments you typically made in your manual reviews (e.g., correctness, performance, security, naming, test gaps, API shape, UX, docs).
> TODO 

b. A comparison of **your** comments vs. **Graphite’s** AI-generated comments for each PR.
> TODO

c. When the AI reviews were better/worse than yours (cite specific examples)
> TODO

d. Your comfort level trusting AI reviews going forward and any heuristics for when to rely on them.
>TODO 



