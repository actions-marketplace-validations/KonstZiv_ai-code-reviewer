# Sprint Beta-0 — After-Review Backlog

Tasks and improvements discovered during code review that are out of scope
for the current sprint. To be triaged after sprint completion.

---

## 1. Detect "go modules" as package_manager in CIPipelineAnalyzer

**Source:** PR review of task 4.1 fixture tests
**Priority:** Low
**Type:** Enhancement

`CIPipelineAnalyzer` does not recognize Go modules as a package manager.
When analyzing a Go project with `.gitlab-ci.yml` containing `go test`,
`go vet`, etc., the `package_manager` field in `CIInsights` remains `None`.

**Expected:** When a Go CI config uses `go` commands or the repository
contains `go.mod`, set `package_manager = "go modules"`.

**Where:** `src/ai_reviewer/discovery/ci_analyzer.py` — add detection for
Go modules from CI commands (`go mod`, `go build`, `go test`) or from
`go.mod` presence in the file tree at the orchestrator level.

**Note:** The `go_gitlab` test fixture currently expects `null` for
`package_manager` — update it when this is implemented.
